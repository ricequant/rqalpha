from enum import Enum
from operator import itemgetter
from typing import Dict, Mapping, NamedTuple, Optional, Union, cast, List, Tuple

from numpy import inf, sign
from numpy import round as np_round
from pandas import DataFrame, Index, Series

from rqalpha.api import export_as_api
from rqalpha.const import (
    DEFAULT_ACCOUNT_TYPE,
    EXECUTION_PHASE,
    INSTRUMENT_TYPE,
    MARKET,
    POSITION_DIRECTION,
    POSITION_EFFECT,
    SIDE,
)
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.mod.rqalpha_mod_sys_risk.validators.cash_validator import validate_cash
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders import (
    AbstractStockTransactionCostDecider,
)
from rqalpha.model.order import AlgoOrder, LimitOrder, MarketOrder, Order, OrderStyle
from rqalpha.portfolio.account import Account
from rqalpha.utils.arg_checker import assure_active_instrument
from rqalpha.utils.exception import RQApiNotSupportedError, RQInvalidArgument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _, lazy_gettext
from rqalpha.utils.price_limits import reaches_limit_down_vectorized, reaches_limit_up_vectorized


class AdjustingResult(NamedTuple):
    adjustments: Series
    denials: Dict[str, str]
    """denials: key 为 order_book_id，value 为 DenialReason.translation（见 DenialReason 枚举）"""


class ExchangeRatePair(NamedTuple):
    ask: float
    bid: float

    @property
    def middle(self):
        return (self.bid + self.ask) / 2


class CommentedEnum(str, Enum):
    _translation_key: str

    def __new__(cls, value, translation_key: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._translation_key = translation_key
        return obj

    @property
    def translation(self) -> str:
        """Lazy translation - evaluates at access time using current locale"""
        return _(self._translation_key)


class DenialReason(CommentedEnum):
    less_than_half = 'less_than_half', lazy_gettext('Order creation failed: quantity less than half of minimum order quantity')
    suspended_buy = 'suspended_buy', lazy_gettext('Order creation failed: cannot buy due to suspension')
    suspended_sell = 'suspended_sell', lazy_gettext('Order creation failed: cannot sell due to suspension')
    no_price = 'no_price', lazy_gettext('Order creation failed: no market data available')
    limit_up_buy = 'limit_up_buy', lazy_gettext('Order creation failed: cannot buy due to limit up')
    limit_up_sell = 'limit_up_sell', lazy_gettext('Order creation failed: cannot sell due to limit up')
    limit_down_buy = 'limit_down_buy', lazy_gettext('Order creation failed: cannot buy due to limit down')
    limit_down_sell = 'limit_down_sell', lazy_gettext('Order creation failed: cannot sell due to limit down')
    closable_exceeded = 'closable_exceeded', lazy_gettext('Order creation failed: insufficient closable position')


SUPPORTED_INSTRUMENT_TYPES = {
    INSTRUMENT_TYPE.CS,
    INSTRUMENT_TYPE.CONVERTIBLE,
    INSTRUMENT_TYPE.ETF,
    INSTRUMENT_TYPE.LOF,
    INSTRUMENT_TYPE.REITs,
}


class OrderTargetPortfolio:
    def __init__(
        self,
        account: Account,
        target_weights: Series,
        valuation_prices: Optional[Series],
        env: Environment,
    ):
        quantities, closable = {}, {}
        for position in account.get_positions():
            quantities[position.order_book_id] = position.quantity
            closable[position.order_book_id] = position.closable
        current_quantities = Series(quantities, dtype=int)
        current_closable = Series(closable, dtype=int)
        index = Index(target_weights.index.union(current_quantities.index).union(current_closable.index))
        if valuation_prices is not None:
            valuation_prices = valuation_prices.reindex(index)
            if valuation_prices.isna().any():
                raise RQInvalidArgument(
                    _('prices of {} is not provided').format(valuation_prices.isna().index[valuation_prices.isna()])
                )
        self._target_weights = target_weights.reindex(index, fill_value=0)
        self._current_quantities = current_quantities.reindex(index, fill_value=0)
        self._current_closable = current_closable.reindex(index, fill_value=0)

        self._env = env

        instruments = env.data_proxy.get_active_instruments(index, env.trading_dt)
        for i in instruments.values():
            if i.type not in SUPPORTED_INSTRUMENT_TYPES:
                raise RQApiNotSupportedError(_('instrument type {} is not supported').format(i.type))

        self._market = Series({i.order_book_id: i.market for i in instruments.values()}, dtype='object')
        self._tick_sizes = Series({i: env.data_proxy.get_tick_size(i) for i in index}, dtype=float)
        self._min_qty = Series(
            {i.order_book_id: i.min_order_quantity for i in instruments.values()},
            dtype='int64',
        )
        self._step_size = Series(
            {i.order_book_id: i.order_step_size for i in instruments.values()},
            dtype='int64',
        )
        self._suspended = Series(
            {i: env.data_proxy.is_suspended(i, env.trading_dt) for i in index},
            dtype=bool,
        )

        exchange_rate_middle = Series(index=index, dtype=float)
        self._exchange_rates: Dict[MARKET, ExchangeRatePair] = {}
        for market, group in self._market.groupby(by=self._market):
            market = cast(MARKET, market)
            exchange_rate = env.data_proxy.get_exchange_rate(env.trading_dt.date(), market)
            pair = ExchangeRatePair(ask=exchange_rate.ask_reference, bid=exchange_rate.bid_reference)
            exchange_rate_middle[group.index] = pair.middle
            self._exchange_rates[market] = pair

        phase = ExecutionContext.phase()
        self._prices = DataFrame(index=index, columns=['last', 'limit_up', 'limit_down'], dtype=float)  # type: ignore
        if phase == EXECUTION_PHASE.OPEN_AUCTION:
            # 集合竞价阶段，最近的价格是昨收
            if valuation_prices is not None:
                self._prices['last'] = valuation_prices
            else:
                prev_date = env.data_proxy.get_previous_trading_date(env.trading_dt)
                for order_book_id in index:
                    bar = env.data_proxy.get_bar(order_book_id, prev_date, '1d')
                    if bar.isnan:
                        raise RuntimeError('missing valuation prices: {}'.format(order_book_id))
                    self._prices.loc[order_book_id, 'last'] = bar.close
        elif phase == EXECUTION_PHASE.ON_BAR:
            if env.config.base.frequency == '1d':
                # TODO：根据算法时间选择最近的分钟线作为估值
                # 当前先选择开盘价
                for order_book_id in index:
                    bar = env.data_proxy.get_bar(order_book_id, env.trading_dt, '1d')
                    if bar.isnan:
                        raise RuntimeError('missing valuation prices: {}'.format(order_book_id))
                    self._prices.loc[order_book_id] = [bar.open, bar.limit_up, bar.limit_down]
                if valuation_prices is not None:
                    self._prices['last'] = valuation_prices
            elif env.config.base.frequency == '1m':
                raise NotImplementedError
            else:
                raise RQApiNotSupportedError(_('frequency {} is not supported').format(env.config.base.frequency))
        else:
            raise RQApiNotSupportedError(_('not supported to be called in {} phase').format(phase))
        self._prices_settle_ccy = self._prices['last'] * exchange_rate_middle
        if self._prices_settle_ccy.isna().any():
            missing_prices = self._prices_settle_ccy[self._prices_settle_ccy.isna()]
            raise RecursionError('missing valuation prices: {}'.format(missing_prices.index.to_list()))
        # 排除未来数据影响，使用 valuation_prices 重新计算估值
        self._total_value = (
            account.total_value
            - account.market_value
            + current_quantities.mul(self._prices_settle_ccy, fill_value=0).sum()
        )
        # TODO: 分别计算 A H 股的可用资金
        self._cash_available = account.cash

    def _round_adjusting_odd_lots(self, adjusting: Series) -> Tuple[Series, Dict[DenialReason, Series]]:
        # 调仓量不足最小挂单量一半的设为0
        min_qty = self._min_qty
        lot_size = self._step_size
        positions = self._current_quantities
        less_than_half = (adjusting.abs() < (min_qty / 2)) & (-adjusting != positions)
        less_than_half_denial = less_than_half & (adjusting != 0)
        adjusting[less_than_half] = 0

        # 调仓量不足最小挂单量但高于一半的设为最小挂单量
        lt_min_qty_gte_half = (
            (adjusting.abs() >= (min_qty / 2)) & (adjusting.abs() < min_qty) & (-adjusting != positions)
        )
        adjusting[lt_min_qty_gte_half] = (min_qty * sign(adjusting))[lt_min_qty_gte_half]

        # 调仓量超过最小挂单量的按 lot_size 四舍五入进行 round
        gte_min_qty = (adjusting.abs() >= min_qty) & (-adjusting != positions)
        adjusting[gte_min_qty] = (np_round((adjusting / lot_size).astype(float)) * lot_size)[gte_min_qty]
        adjusting[(adjusting < 0) & (-adjusting > positions)] = -positions
        return adjusting, {DenialReason.less_than_half: less_than_half_denial}

    def _calc_adjusting(
        self, target_quantities: Series, direction: POSITION_DIRECTION
    ) -> Tuple[Series, Dict[DenialReason, Series]]:
        # caller should ensure the index of diff, price_df and suspended are the same
        diff, denials = self._round_adjusting_odd_lots(target_quantities.sub(self._current_quantities, fill_value=0))
        prices, limit_up, limit_down = itemgetter('last', 'limit_up', 'limit_down')(self._prices)
        adjusting_denied = (
            self._suspended  # 停牌
            | prices.isna()  # 无行情
        )

        denials[DenialReason.suspended_buy] = (diff > 0) & self._suspended
        denials[DenialReason.suspended_sell] = (diff < 0) & self._suspended
        denials[DenialReason.no_price] = prices.isna() & (diff != 0)

        limit_up = reaches_limit_up_vectorized(prices, limit_up, self._tick_sizes)
        limit_down = reaches_limit_down_vectorized(prices, limit_down, self._tick_sizes)
        if direction == POSITION_DIRECTION.LONG:
            # 涨停不能开、跌停不能平
            limit_buy = (diff > 0) & limit_up
            limit_sell = (diff < 0) & limit_down
            denials[DenialReason.limit_up_buy] = limit_buy
            denials[DenialReason.limit_down_sell] = limit_sell
        else:
            # 跌停不能开、涨停不能平
            limit_buy = (diff > 0) & limit_down
            limit_sell = (diff < 0) & limit_up
            denials[DenialReason.limit_down_buy] = limit_buy
            denials[DenialReason.limit_up_sell] = limit_sell
        adjusting_denied |= limit_buy
        adjusting_denied |= limit_sell
        diff[adjusting_denied] = 0

        closable_exceeded = diff.add(self._current_closable, fill_value=0) < 0
        diff[closable_exceeded] = -self._current_closable  # 可平仓位
        denials[DenialReason.closable_exceeded] = closable_exceeded & (self._current_closable == 0)
        return diff, denials

    @staticmethod
    def _format_denials(denials: Dict[DenialReason, Series]) -> Dict[str, str]:
        denial_reason_details: Dict[str, str] = {}
        for reason, mask in denials.items():
            for obid in mask[mask].index:
                denial_reason_details[obid] = reason.translation
        return denial_reason_details

    @lru_cache(maxsize=8)
    def _trans_cost_decider(self, market: MARKET) -> AbstractStockTransactionCostDecider:
        decider = self._env.get_transaction_cost_decider(INSTRUMENT_TYPE.CS, market)
        if not isinstance(decider, AbstractStockTransactionCostDecider):
            raise RuntimeError(
                'transaction cost decider for market {} is not a subclass of AbstractStockTransactionCostDecider'.format(
                    market
                )
            )
        return decider

    SAFETY: float = 1.2

    def __call__(self, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG) -> AdjustingResult:
        if self._current_quantities.empty and self._target_weights.empty:
            return AdjustingResult(adjustments=Series(dtype='float64'), denials=dict())

        if self._target_weights.sum() > 0.95:
            # 如果目标是满仓或者接近满仓，则使用一个较高的 safety 开始下降
            safety = self.SAFETY
        else:
            safety = 1.
        last_proportion_diff = inf
        last_diff = None
        last_denials = None
        prices = self._prices_settle_ccy
        while True:
            if safety < 0:
                # 防止 bug 导致的死循环
                raise RuntimeError('safety < 0: {}'.format(safety))
            target_quantities: Series = (self._total_value * safety * self._target_weights / prices).round(0)
            diff, denials = self._calc_adjusting(target_quantities, direction)

            delta_mv = diff * prices
            cash_consumed = delta_mv.sum()
            for market, group in self._market.groupby(by=self._market):
                # 税费等成本
                cash_consumed += (
                    self._trans_cost_decider(market).batch_estimate(diff[group.index], prices[group.index]).sum()
                )  # type: ignore
                # 汇率成本
                if market != MARKET.CN:
                    exchange_rate = self._exchange_rates[market]  # type: ignore
                    cash_consumed += delta_mv[(diff > 0) & (diff.index.isin(group.index))].sum() * (
                        exchange_rate.ask / exchange_rate.middle - 1
                    )
                    cash_consumed += delta_mv[(diff < 0) & (diff.index.isin(group.index))].sum() * (
                        exchange_rate.middle / exchange_rate.bid - 1
                    )

            total_proportion = ((self._current_quantities.add(diff, fill_value=0)) * prices).sum() / self._total_value
            proportion_diff = abs(total_proportion - self._target_weights.sum())
            if cash_consumed < self._cash_available:
                # TODO: 分别计算 A H 股的可用资金
                if proportion_diff > last_proportion_diff and last_diff is not None and last_denials is not None:
                    break
                last_diff, last_denials = diff, denials
            last_proportion_diff = proportion_diff
            safety -= min(max(proportion_diff / 10, 0.0001), 0.002)
        return AdjustingResult(adjustments=last_diff, denials=self._format_denials(last_denials))


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
)
def order_target_portfolio_smart(
    target_portfolio: Union[Mapping[str, float], Series],
    order_prices: Optional[Union[AlgoOrder, Mapping[str, float], Series]] = None,
    valuation_prices: Optional[Union[Mapping[str, float], Series]] = None,
) -> Dict[str, Union[Order, str]]:
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

    :return: 字典（key 为 order_book_id，value 为 Order 对象或拒单原因字符串）
    :rtype: Dict

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
    target_weights = Series(
        {assure_active_instrument(id_or_ins).order_book_id: percent for id_or_ins, percent in target_portfolio.items()},
        dtype=float,
    )
    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    if isinstance(order_prices, (Mapping, Series)):
        style_map: Dict[str, OrderStyle] = {
            cast(str, order_book_id): LimitOrder(price) for order_book_id, price in order_prices.items()
        }

        def _get_style(order_book_id) -> OrderStyle:
            try:
                return style_map[order_book_id]
            except KeyError:
                raise RQInvalidArgument(
                    _('price of {} is needed, which is not provided in the algo_or_prices').format(order_book_id)
                )
    else:
        style = order_prices or MarketOrder()
        _get_style = lambda order_book_id: style

    if valuation_prices is not None:
        prices = Series(valuation_prices)
    else:
        prices = None

    if target_weights[target_weights < 0].any():
        raise ValueError('target_weights contains negative value: {}'.format(target_weights[target_weights < 0]))

    result = OrderTargetPortfolio(
        account=account,
        target_weights=Series(target_weights),
        valuation_prices=prices,
        env=env,
    )()

    adjusting = result.adjustments
    denials = dict(result.denials) if result.denials else {}

    results: Dict[str, Union[Order, str]] = {}

    # 先将拒单原因加入结果
    results.update(denials)

    # 先平
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting < 0])).items():
        order = env.submit_order(
            Order.__from_create__(
                order_book_id,
                abs(delta_quantity),
                SIDE.SELL,
                _get_style(order_book_id),
                POSITION_EFFECT.CLOSE,
            )
        )
        if order is not None:
            results[order_book_id] = order
    # 后开
    for order_book_id, delta_quantity in cast(Series, (adjusting[adjusting > 0])).items():
        order_book_id = cast(str, order_book_id)
        order_to_be_submitted = Order.__from_create__(
            order_book_id,
            delta_quantity,
            SIDE.BUY,
            _get_style(order_book_id),
            POSITION_EFFECT.OPEN,
        )
        if validate_cash(env, order_to_be_submitted, account.cash) is not None:
            # 因为资金不够而下单失败，使用剩余资金下单
            order = _order_value(
                account,
                account.get_position(order_book_id),
                order_book_id,
                account.cash,
                _get_style(order_book_id),
                zero_amount_as_exception=False,
            )
        else:
            order = env.submit_order(order_to_be_submitted)
        if order is not None:
            results[order_book_id] = order
    return results
