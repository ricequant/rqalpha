from enum import Enum
from operator import itemgetter
from typing import Dict, Mapping, NamedTuple, Optional, Tuple, Union, cast

from numpy import inf, isnan, sign
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
from rqalpha.utils import are_valid_prices
from rqalpha.utils.arg_checker import assure_active_instrument
from rqalpha.utils.exception import RQApiNotSupportedError, RQInvalidArgument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.i18n import lazy_gettext
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
    less_than_half = (
        'less_than_half',
        lazy_gettext('Order creation failed: quantity less than half of minimum order quantity'),
    )
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
        """计算调仓数量并应用各类约束。

        Returns:
            (diff, denials): 调整后的数量变化和各类拒绝原因
        """
        diff, denials = self._round_adjusting_odd_lots(target_quantities.sub(self._current_quantities, fill_value=0))
        prices, limit_up, limit_down = itemgetter('last', 'limit_up', 'limit_down')(self._prices)

        # 构建完全不可调整的资产掩码（停牌、无行情）
        adjusting_denied = (
            self._suspended  # 停牌
            | prices.isna()  # 无行情
        )

        # 记录各类拒绝原因（用于向用户报告）
        denials[DenialReason.suspended_buy] = (diff > 0) & self._suspended
        denials[DenialReason.suspended_sell] = (diff < 0) & self._suspended
        denials[DenialReason.no_price] = prices.isna() & (diff != 0)

        # 涨跌停限制（方向相关）
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

    def _estimate_transaction_costs(self, diff: Series, prices: Series) -> float:
        """估算交易成本（手续费 + 汇率成本）。"""
        delta_mv = diff * prices
        costs = 0.0
        for market, group in self._market.groupby(by=self._market):
            # 税费等成本
            costs += self._trans_cost_decider(market).batch_estimate(diff[group.index], prices[group.index]).sum()  # type: ignore
            if market != MARKET.CN:
                # 汇率成本
                exchange_rate = self._exchange_rates[market]  # type: ignore
                buy_mask = (diff > 0) & (diff.index.isin(group.index))
                sell_mask = (diff < 0) & (diff.index.isin(group.index))
                costs += delta_mv[buy_mask].sum() * (exchange_rate.ask / exchange_rate.middle - 1)
                costs += delta_mv[sell_mask].sum() * (exchange_rate.middle / exchange_rate.bid - 1)
        return costs

    def _calc_min_adjustable(self, denials: Dict[DenialReason, Series], prices: Series) -> float:
        """计算最小可调精度，仅基于可调资产（排除所有拒绝的资产）。无可调资产时返回 inf 触发退出。"""
        adjusting_denied = Series(False, index=prices.index)
        for reason, mask in denials.items():
            adjusting_denied |= mask
        can_adjust = ~adjusting_denied
        if can_adjust.any():
            return (self._min_qty[can_adjust] * prices[can_adjust] / self._total_value).min()
        return inf

    MAX_ITERATIONS: int = 150
    KP_INIT: float = 0.382  # 比例增益初始值（黄金分割比）
    KP_MIN: float = 0.01  # 比例增益下限
    KP_DECAY: float = 0.382  # 振荡时 kp 衰减因子
    PRECISION: float = 0.0001  # 硬性精度要求（万分之一）
    MAX_OSCILLATIONS: int = 10  # kp 达到下限后允许的最大振荡次数

    def __call__(self, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG) -> AdjustingResult:
        """使用 P 控制器迭代求解最优调仓方案。

        算法核心思路：
        1. 通过 safety 系数缩放目标持仓量，用比例控制器（P-controller）调节 safety 使实际持仓比例逼近目标权重
        2. 仅基于可调资产（排除停牌、涨跌停、不可平仓等）计算最小可调精度，无可调资产时立即退出
        tips:
        1. 误差定义：diff_proportion = 持仓市值 / (总资产 - 交易成本)，将手续费、税费、汇率成本纳入控制目标
        2. 振荡抑制：检测误差符号翻转时降低比例增益 kp，防止在离散约束下来回震荡
        """
        if self._current_quantities.empty and self._target_weights.empty:
            return AdjustingResult(adjustments=Series(dtype='float64'), denials=dict())

        # 初始化 P 控制器状态
        total_target_weight = self._target_weights.sum()
        safety = 1.0  # 目标持仓缩放系数，通过迭代调节逼近目标权重
        kp = self.KP_INIT  # 比例增益，控制每次 safety 调整幅度
        prev_error = 0.0  # 上一次带符号误差，用于振荡检测
        oscillation_count = 0  # 振荡次数，误差符号翻转时累加

        # 历史最优可行解
        best_error = inf
        best_diff = Series(dtype='float64')
        best_denials = None
        prices = self._prices_settle_ccy

        for iteration in range(self.MAX_ITERATIONS):
            # 1. 根据当前 safety 计算目标持仓量，并应用各类约束
            target_quantities: Series = (self._total_value * safety * self._target_weights / prices).round(0)
            diff, denials = self._calc_adjusting(target_quantities, direction)

            # 2. 计算交易成本和现金消耗
            transaction_costs = self._estimate_transaction_costs(diff, prices)
            cash_consumed = (diff * prices).sum() + transaction_costs

            # 3. 计算成本感知误差
            # signed_error > 0 表示实际比例低于目标，需增大 safety；反之需减小
            total_market_value = ((self._current_quantities.add(diff, fill_value=0)) * prices).sum()
            diff_proportion = total_market_value / (self._total_value - transaction_costs)
            signed_error = total_target_weight - diff_proportion
            current_error = abs(signed_error)

            # 4. 更新最优可行解
            if current_error < best_error:
                best_error = current_error
                best_diff = diff
                best_denials = denials

            # 5. 振荡检测与 kp 衰减
            if signed_error * prev_error < 0:
                oscillation_count += 1
                kp *= self.KP_DECAY
                kp = max(kp, self.KP_MIN)

            # 检查退出条件
            min_adjustable = self._calc_min_adjustable(denials, prices)
            if (
                cash_consumed < self._cash_available
                # 寻找基于当前可用现金下的最优解
                # TODO: 分别计算 A H 股的可用资金
                and (
                        current_error < min_adjustable
                        or current_error <= self.PRECISION
                )
            ) or (kp <= self.KP_MIN and oscillation_count > self.MAX_OSCILLATIONS):
                break

            # safety 调整量 = kp × 误差
            safety += kp * signed_error
            prev_error = signed_error

        return AdjustingResult(adjustments=best_diff, denials=self._format_denials(best_denials or dict()))


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
    智能批量调整仓位至目标权重，支持股票、指数、场内基金、REITs、可转债。

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
    invalid_order_book_ids = Index([])
    if isinstance(order_prices, (Mapping, Series)):
        normalized_order_prices = Series(
            {assure_active_instrument(order_book_id).order_book_id: price for order_book_id, price in order_prices.items()},
            dtype=object,
        )
        valid_order_price_mask = are_valid_prices(normalized_order_prices)
        invalid_order_book_ids = normalized_order_prices.index[~valid_order_price_mask]
        style_map: Dict[str, OrderStyle] = {
            order_book_id: LimitOrder(price) for order_book_id, price in normalized_order_prices[valid_order_price_mask].items()
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
    if len(invalid_order_book_ids) > 0:
        invalid_price_mask = adjusting.index.isin(invalid_order_book_ids) & (adjusting != 0)
        adjusting.loc[invalid_price_mask] = 0
        denials.update(
            {order_book_id: _('Limit order price is invalid.') for order_book_id in adjusting.index[invalid_price_mask]}
        )

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
