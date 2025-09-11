from typing import Mapping, NamedTuple, cast, Optional, Union
from operator import itemgetter

from pandas import Series, Index, DataFrame
from numpy import sign, round as np_round, inf

from rqalpha.api import export_as_api
from rqalpha.apis.api_base import assure_instrument
from rqalpha.model.order import AlgoOrder, MarketOrder
from rqalpha.model.order import Order
from rqalpha.environment import Environment
from rqalpha.const import EXECUTION_PHASE, POSITION_DIRECTION, INSTRUMENT_TYPE, MARKET, DEFAULT_ACCOUNT_TYPE, SIDE, POSITION_EFFECT
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.utils.exception import RQApiNotSupportedError
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
        target_weights: Series,
        current_quantities: Series,
        current_closable: Series,
        env: Environment,
    ):
        if target_weights[target_weights < 0].any():
            raise ValueError("target_weights contains negative value: {}".format(target_weights[target_weights < 0]))

        index = Index(target_weights.index.union(current_quantities.index).union(current_closable.index))
        self._target_weights = target_weights.reindex(index, fill_value=0)
        self._current_quantities = current_quantities.reindex(index, fill_value=0)
        self._current_closable = current_closable.reindex(index, fill_value=0)

        self._env = env

        instruments = env.data_proxy.multi_instruments(index)
        for i in instruments.values():
            if i.type != INSTRUMENT_TYPE.CS:
                raise RQApiNotSupportedError(_("instrument type {} is not supported").format(i.type))
            
        self._market = Series({i.order_book_id: i.market for i in instruments.values()})
        self._min_qty = Series({i.order_book_id: i.min_order_quantity for i in instruments.values()})
        self._step_size = Series({i.order_book_id: i.order_step_size for i in instruments.values()})
        self._suspended = Series({
            i: env.data_proxy.is_suspended(i, env.trading_dt) for i in index
        })

        exchange_rate_middle = Series(index=index, dtype=float)
        self._exchange_rates: dict[MARKET, ExchangeRatePair] = {}
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
            prev_date = env.data_proxy.get_previous_trading_date(env.trading_dt)
            for order_book_id in index:
                bars = env.data_proxy.history_bars(order_book_id, 1, "1d", ["close"], prev_date)
                self._prices.loc[order_book_id, "last"] = bars["close"][0]
        elif phase == EXECUTION_PHASE.ON_BAR:
            if env.config.base.frequency == "1d":
                # TODO：根据算法时间选择最近的分钟线作为估值
                # 当前先选择开盘价
                for order_book_id in index:
                    bars = env.data_proxy.history_bars(order_book_id, 1, "1d", ["open", "limit_up", "limit_down"], env.trading_dt)
                    self._prices.loc[order_book_id] = bars[0]
            elif env.config.base.frequency == "1m":
                raise NotImplementedError
            else:
                raise RQApiNotSupportedError(_("frequency {} is not supported").format(env.config.base.frequency))
        else:
            raise RQApiNotSupportedError(_("not supported to be called in {} phase").format(phase))
        self._prices_settle_ccy = self._prices["last"] * exchange_rate_middle

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

    def __call__(
        self, target_value: float, cash_available: float, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG, 
    ) -> Series:
        
        if self._current_quantities.empty and self._target_weights.empty:
            return Series()
     
        safety = self.SAFETY
        last_proportion_diff = inf
        last_diff = None
        prices = self._prices_settle_ccy
        while True:
            if safety < 0:
                # 防止 bug 导致的死循环
                raise RuntimeError("safety < 0: {}".format(safety))
            target_quantities: Series = (target_value * safety * self._target_weights / prices).round(0)
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

            total_proportion = ((self._current_quantities.add(diff, fill_value=0)) * prices).sum() / target_value
            proportion_diff = abs(total_proportion - self._target_weights.sum())
            if cash_consumed < cash_available:
                # TODO: 分别计算 A H 股的可用资金
                if proportion_diff >= last_proportion_diff and last_diff is not None:
                    return last_diff
                last_diff = diff
            last_proportion_diff = proportion_diff
            safety -= min(max(proportion_diff / 10, 0.0001), 0.002)
            

@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
)
def order_target_portfolio_smart(target_portfolio: Union[Mapping[str, float], Series], algo: Optional[AlgoOrder] = None):
    from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import _order_value

    env = Environment.get_instance()
    target_weights = {
        assure_instrument(id_or_ins).order_book_id: percent for id_or_ins, percent in target_portfolio.items()
    }
    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    quantities, closable = {},  {}
    for position in account.get_positions():
        quantities[position.order_book_id] = position.quantity
        closable[position.order_book_id] = position.closable
    adjusting = OrderTargetPortfolio(
        target_weights=Series(target_weights),
        current_quantities=Series(quantities),
        current_closable=Series(closable),
        env=env
    )(
        target_value = env.portfolio.total_value,
        cash_available = account.cash,
    )

    orders = []
    style = algo or MarketOrder()
    # 先平
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting < 0])).items():
        order = env.submit_order(Order.__from_create__(
            order_book_id,
            abs(delta_quantity),
            SIDE.SELL,
            style,
            POSITION_EFFECT.CLOSE
        ))
        if order is not None:
            orders.append(order)
    # 后开
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting > 0])).items():
        order_book_id = cast(str, order_book_id)
        order_to_be_submitted = Order.__from_create__(
            order_book_id,
            delta_quantity,
            SIDE.BUY,
            style,
            POSITION_EFFECT.OPEN
        )
        order = env.submit_order(order_to_be_submitted)
        if order is None:
            if validate_cash(env, order_to_be_submitted, account.cash) is not None:
                # 因为资金不够而下单失败，使用剩余资金下单
                order = _order_value(
                    account, 
                    account.get_position(order_book_id), 
                    env.data_proxy.instrument_not_none(order_book_id), 
                    account.cash, 
                    style, 
                    zero_amount_as_exception=False
                )
        if order is not None:
            orders.append(order)
    return orders
