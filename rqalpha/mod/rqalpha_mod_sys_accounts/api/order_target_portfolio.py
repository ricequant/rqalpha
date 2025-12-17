from typing import Mapping, NamedTuple, cast, Optional, Union, Dict
from collections import defaultdict
from operator import itemgetter

from pandas import Series, Index, DataFrame
from numpy import sign, round as np_round, inf

from rqalpha.api import export_as_api
from rqalpha.utils.arg_checker import assure_active_instrument
from rqalpha.model.order import AlgoOrder, MarketOrder, LimitOrder, OrderStyle
from rqalpha.model.order import Order
from rqalpha.environment import Environment
from rqalpha.const import EXECUTION_PHASE, POSITION_DIRECTION, INSTRUMENT_TYPE, MARKET, DEFAULT_ACCOUNT_TYPE, SIDE, POSITION_EFFECT
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.portfolio.account import Account
from rqalpha.utils.exception import RQApiNotSupportedError, RQInvalidArgument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _

from rqalpha.mod.rqalpha_mod_sys_risk.validators.cash_validator import validate_cash
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders import AbstractStockTransactionCostDecider


class ExchangeRatePair(NamedTuple):
    ask: float
    bid: float

    @property
    def middle(self):
        return (self.bid + self.ask) / 2


class OrderTargetPortfolio:
    def __init__(
        self,
        account: Account,
        target_weights: Series,
        valuation_prices: Optional[Series],
        env: Environment,
    ):
        quantities, closable = {},  {}
        for position in account.get_positions():
            quantities[position.order_book_id] = position.quantity
            closable[position.order_book_id] = position.closable
        current_quantities = Series(quantities, dtype=int)
        current_closable = Series(closable, dtype=int)
        index = Index(target_weights.index.union(current_quantities.index).union(current_closable.index))
        if valuation_prices is not None:
            valuation_prices = valuation_prices.reindex(index)
            if valuation_prices.isna().any():
                raise RQInvalidArgument(_("prices of {} is not provided").format(valuation_prices.isna().index[valuation_prices.isna()]))
        self._target_weights = target_weights.reindex(index, fill_value=0)
        self._current_quantities = current_quantities.reindex(index, fill_value=0)
        self._current_closable = current_closable.reindex(index, fill_value=0)

        self._env = env

        instruments = env.data_proxy.get_listed_instruments(index, env.trading_dt)
        for i in instruments.values():
            if i.type != INSTRUMENT_TYPE.CS:
                raise RQApiNotSupportedError(_("instrument type {} is not supported").format(i.type))
            
        self._market = Series({i.order_book_id: i.market for i in instruments.values()}, dtype="object")
        self._min_qty = Series({i.order_book_id: i.min_order_quantity for i in instruments.values()}, dtype="int64")
        self._step_size = Series({i.order_book_id: i.order_step_size for i in instruments.values()}, dtype="int64")
        self._suspended = Series({
            i: env.data_proxy.is_suspended(i, env.trading_dt) for i in index
        }, dtype=bool)

        exchange_rate_middle = Series(index=index, dtype=float)
        self._exchange_rates: Dict[MARKET, ExchangeRatePair] = {}
        for market, group in self._market.groupby(by=self._market):
            market = cast(MARKET, market)
            exchange_rate = env.data_proxy.get_exchange_rate(env.trading_dt.date(), market)
            pair = ExchangeRatePair(
                ask=exchange_rate.ask_reference,
                bid=exchange_rate.bid_reference
            )
            exchange_rate_middle[group.index] = pair.middle
            self._exchange_rates[market] = pair  

        phase = ExecutionContext.phase()
        self._prices = DataFrame(index=index, columns=["last", "limit_up", "limit_down"], dtype=float)   # type: ignore
        if phase == EXECUTION_PHASE.OPEN_AUCTION:
            # 集合竞价阶段，最近的价格是昨收
            if valuation_prices is not None:
                self._prices["last"] = valuation_prices
            else:
                prev_date = env.data_proxy.get_previous_trading_date(env.trading_dt)
                for order_book_id in index:
                    bars = env.data_proxy.history_bars(order_book_id, 1, "1d", ["close"], prev_date)
                    if bars is None:
                        raise RuntimeError("missing valuation prices: {}".format(order_book_id))
                    self._prices.loc[order_book_id, "last"] = bars["close"][0]
        elif phase == EXECUTION_PHASE.ON_BAR:
            if env.config.base.frequency == "1d":
                # TODO：根据算法时间选择最近的分钟线作为估值
                # 当前先选择开盘价
                for order_book_id in index:
                    bars = env.data_proxy.history_bars(order_book_id, 1, "1d", ["open", "limit_up", "limit_down"], env.trading_dt)
                    if bars is None:
                        raise RuntimeError("missing valuation prices: {}".format(order_book_id))
                    self._prices.loc[order_book_id] = list(bars[0])
                if valuation_prices is not None:
                    self._prices["last"] = valuation_prices
            elif env.config.base.frequency == "1m":
                raise NotImplementedError
            else:
                raise RQApiNotSupportedError(_("frequency {} is not supported").format(env.config.base.frequency))
        else:
            raise RQApiNotSupportedError(_("not supported to be called in {} phase").format(phase))
        self._prices_settle_ccy = self._prices["last"] * exchange_rate_middle
        if self._prices_settle_ccy.isna().any():
            missing_prices = self._prices_settle_ccy[self._prices_settle_ccy.isna()]
            raise RecursionError("missing valuation prices: {}".format(missing_prices.index.to_list()))
        # 排除未来数据影响，使用 valuation_prices 重新计算估值
        self._total_value = account.total_value - account.market_value + current_quantities.mul(self._prices_settle_ccy, fill_value=0).sum()
         # TODO: 分别计算 A H 股的可用资金
        self._cash_available = account.cash

    def _round_adjusting_odd_lots(self, adjusting: Series) -> Series:
        # 调仓量不足最小挂单量一半的设为0
        min_qty = self._min_qty
        lot_size = self._step_size
        positions = self._current_quantities
        adjusting[(adjusting.abs() < (min_qty / 2)) & (-adjusting != positions)] = 0

        # 调仓量不足最小挂单量但高于一半的设为最小挂单量
        lt_min_qty_gte_half = (adjusting.abs() >= (min_qty / 2)) & (adjusting.abs() < min_qty) & (-adjusting != positions)
        adjusting[lt_min_qty_gte_half] = (min_qty * sign(adjusting))[lt_min_qty_gte_half]
        
        # 调仓量超过最小挂单量的按 lot_size 四舍五入进行 round
        gte_min_qty = (adjusting.abs() >= min_qty) & (-adjusting != positions)
        adjusting[gte_min_qty] = (np_round((adjusting / lot_size).astype(float)) * lot_size)[gte_min_qty]
        adjusting[(adjusting < 0) & (-adjusting > positions)] = -positions
        return adjusting

    def _calc_adjusting(self, target_quantities: Series, direction: POSITION_DIRECTION) -> Series:
        # caller should ensure the index of diff, price_df and suspended are the same
        diff = self._round_adjusting_odd_lots(target_quantities.sub(self._current_quantities, fill_value=0))
        prices, limit_up, limit_down = itemgetter("last", "limit_up", "limit_down")(self._prices)
        adjusting_denied = (
            self._suspended |                                              # 停牌
            prices.isna()                                             # 无行情
        )
        limit_up = ~(limit_up.isna()) & (prices >= limit_up)
        limit_down = ~(limit_down.isna()) & (prices <= limit_down)
        if direction == POSITION_DIRECTION.LONG:
            # 涨停不能开、跌停不能平
            adjusting_denied |= ((diff > 0) & (limit_up))
            adjusting_denied |= ((diff < 0) & (limit_down))
        else:
            # 跌停不能开、涨停不能平
            adjusting_denied |= ((diff > 0) & (limit_down))
            adjusting_denied |= ((diff < 0) & (limit_up))
        diff[adjusting_denied] = 0

        diff[diff.add(self._current_closable, fill_value=0) < 0] = -self._current_closable # 可平仓位
        return diff

    @lru_cache(maxsize=8)
    def _trans_cost_decider(self, market: MARKET) -> AbstractStockTransactionCostDecider:
        decider = self._env.get_transaction_cost_decider(INSTRUMENT_TYPE.CS, market)
        if not isinstance(decider, AbstractStockTransactionCostDecider):
            raise RuntimeError("transaction cost decider for market {} is not a subclass of AbstractStockTransactionCostDecider".format(market))
        return decider

    SAFETY: float = 1.2

    def __call__(self, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG) -> Series:
        if self._current_quantities.empty and self._target_weights.empty:
            return Series(dtype="float64")

        if self._target_weights.sum() > 0.95:
            # 如果目标是满仓或者接近满仓，则使用一个较高的 safety 开始下降
            safety = self.SAFETY
        else:
            safety = 1.
        last_proportion_diff = inf
        last_diff = None
        prices = self._prices_settle_ccy
        while True:
            if safety < 0:
                # 防止 bug 导致的死循环
                raise RuntimeError("safety < 0: {}".format(safety))
            target_quantities: Series = (self._total_value * safety * self._target_weights / prices).round(0)
            diff = self._calc_adjusting(target_quantities, direction)

            delta_mv = diff * prices
            cash_consumed = delta_mv.sum()
            for market, group in self._market.groupby(by=self._market):
                # 税费等成本
                cash_consumed += self._trans_cost_decider(market).batch_estimate(diff[group.index], prices[group.index]).sum()  # type: ignore
                # 汇率成本
                if market != MARKET.CN:
                    exchange_rate = self._exchange_rates[market]  # type: ignore
                    cash_consumed += delta_mv[(diff > 0) & (diff.index.isin(group.index))].sum() * (exchange_rate.ask / exchange_rate.middle - 1)
                    cash_consumed += delta_mv[(diff < 0) & (diff.index.isin(group.index))].sum() * (exchange_rate.middle / exchange_rate.bid - 1)

            total_proportion = ((self._current_quantities.add(diff, fill_value=0)) * prices).sum() / self._total_value
            proportion_diff = abs(total_proportion - self._target_weights.sum())
            if cash_consumed < self._cash_available:
                # TODO: 分别计算 A H 股的可用资金
                if proportion_diff > last_proportion_diff and last_diff is not None:
                    return last_diff
                last_diff = diff
            last_proportion_diff = proportion_diff
            safety -= min(max(proportion_diff / 10, 0.0001), 0.002)
            

@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
)
def order_target_portfolio_smart(
    target_portfolio: Union[Mapping[str, float], Series], 
    order_prices: Optional[Union[AlgoOrder, Mapping[str, float], Series]] = None,
    valuation_prices: Optional[Union[Mapping[str, float], Series]] = None,
):
    """
    智能批量调整股票仓位至目标权重。

    :param target_portfolio: 目标权重字典或 Series，key 为 order_book_id，value 为权重
    :param order_prices: 挂单/撮合价格设置，支持以下格式：
                        - None: 使用开盘价（open_auction 中）或收盘价（handle_bar 中）撮合
                        - AlgoOrder: 使用算法单价格撮合（如 VWAPOrder、TWAPOrder）
                        - Dict/Series: 自定义价格挂单/撮合
    :param valuation_prices: 估值价格设置，即交易前调仓算法所能获取到的最新价格，算法将基于该价格计算目标下单量。
                        - None：使用 prev_close（open_auction 中）或 open（handle_bar 中）计算估值
                        - Dict/Series: 自定义算法可获取到的最新价格

    :return: 提交的订单列表
    :rtype: List[Order]

    :example:

    .. code-block:: python

        # 基础用法：默认价格调仓
        order_target_portfolio_smart({
            '000001.XSHE': 0.3,   # 平安银行 30%
            '600000.XSHG': 0.2    # 浦发银行 20%
        })

        # 使用算法单调仓
        order_target_portfolio_smart({
            '000001.XSHE': 0.3,
            '600000.XSHG': 0.2
        }, order_prices=VWAPOrder(930, 940))  # 9:30-9:40 VWAP

        # 指定价格挂单/撮合
        order_target_portfolio_smart({
            '000001.XSHE': 0.3,
            '600000.XSHG': 0.2
        }, order_prices={
            '000001.XSHE': 14.5,  # 限价 14.5 元
            '00700.XHKG': 400     # 限价 400 港元
        })

        # 使用自定义估值价格
        order_target_portfolio_smart({
            '000001.XSHE': 0.3,
            '600000.XSHG': 0.2
        }, 
        order_prices=VWAPOrder(930, 940),
        valuation_prices={
            '000001.XSHE': 14.8,  # 使用模型估值
            '600000.XSHG': 405    # 使用模型估值
        })

    """
    from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import _order_value

    env = Environment.get_instance()
    target_weights = Series({
        assure_active_instrument(id_or_ins).order_book_id: percent for id_or_ins, percent in target_portfolio.items()
    }, dtype=float)
    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    if isinstance(order_prices, (Mapping, Series)):
        style_map: Dict[str, OrderStyle] = {
            cast(str, order_book_id): LimitOrder(price) for order_book_id, price in order_prices.items()
        }
        def _get_style(order_book_id) -> OrderStyle:
            try:
                return style_map[order_book_id]
            except KeyError:
                raise RQInvalidArgument(_("price of {} is needed, which is not provided in the algo_or_prices").format(order_book_id))
    else:
        style = order_prices or MarketOrder()
        _get_style = lambda order_book_id: style

    if valuation_prices is not None:
        prices = Series(valuation_prices)
    else:
        prices = None

    if target_weights[target_weights < 0].any():
        raise ValueError("target_weights contains negative value: {}".format(target_weights[target_weights < 0]))

    adjusting = OrderTargetPortfolio(
        account=account,
        target_weights=Series(target_weights),
        valuation_prices=prices,
        env=env
    )(
    )

    orders = []

    # 先平
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting < 0])).items():
        order = env.submit_order(Order.__from_create__(
            order_book_id, abs(delta_quantity), SIDE.SELL, _get_style(order_book_id), POSITION_EFFECT.CLOSE
        ))
        if order is not None:
            orders.append(order)
    # 后开
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting > 0])).items():
        order_book_id = cast(str, order_book_id)
        order_to_be_submitted = Order.__from_create__(
            order_book_id, delta_quantity, SIDE.BUY, _get_style(order_book_id), POSITION_EFFECT.OPEN
        )
        if validate_cash(env, order_to_be_submitted, account.cash) is not None:
            # 因为资金不够而下单失败，使用剩余资金下单
            order = _order_value(
                account, 
                account.get_position(order_book_id), 
                env.data_proxy.instrument_not_none(order_book_id), 
                account.cash, 
                _get_style(order_book_id), 
                zero_amount_as_exception=False
            )
        else:
            order = env.submit_order(order_to_be_submitted)
        if order is not None:
            orders.append(order)
    return orders
