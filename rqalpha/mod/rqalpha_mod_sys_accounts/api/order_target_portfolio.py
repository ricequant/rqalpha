from enum import Enum
from operator import itemgetter
from typing import Dict, Mapping, NamedTuple, Optional, Tuple, Union, cast

from numpy import inf, isfinite, isinf, isnan, sign
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
        self._no_price = self._prices['last'].isna()
        self._tradable = ~(self._suspended | self._no_price)
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

    def _calc_adjusting_quantities(
        self, target_quantities: Series, direction: POSITION_DIRECTION
    ) -> Tuple[Series, Dict[DenialReason, Series]]:
        """计算数量层面的调仓量，并在股数 round 后做最终交易约束校验。

        Returns:
            (diff, denials): 调整后的数量变化和各类拒绝原因
        """
        diff, denials = self._round_adjusting_odd_lots(target_quantities.sub(self._current_quantities, fill_value=0))
        prices, limit_up, limit_down = itemgetter('last', 'limit_up', 'limit_down')(self._prices)

        # 完全不可调整的资产（停牌、无行情）先拒绝，后续再叠加涨跌停限制。
        adjusting_denied = ~self._tradable

        # 记录各类拒绝原因（用于向用户报告）
        denials[DenialReason.suspended_buy] = (diff > 0) & self._suspended
        denials[DenialReason.suspended_sell] = (diff < 0) & self._suspended
        denials[DenialReason.no_price] = self._no_price & (diff != 0)

        # 权重目标落到股数后会经过 round 和最小下单量处理，实际买卖方向和数量可能变化；
        # 因此数量层仍需对可交易标的做最终涨跌停校验。
        limit_up = self._tradable & reaches_limit_up_vectorized(prices, limit_up, self._tick_sizes)
        limit_down = self._tradable & reaches_limit_down_vectorized(prices, limit_down, self._tick_sizes)
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

    def _current_weights(self, prices: Series) -> Series:
        """按当前估值价格计算持仓权重。"""
        if self._total_value <= 0:
            return Series(0.0, index=self._target_weights.index, dtype=float)
        return self._current_quantities.mul(prices, fill_value=0) / self._total_value

    def _calc_weight_bounds(
        self, direction: POSITION_DIRECTION, prices: Series
    ) -> Tuple[Series, Series, Dict[DenialReason, Series]]:
        """根据单票交易约束计算本次调仓允许到达的权重上下界。"""
        index = self._target_weights.index
        current_weights = self._current_weights(prices)

        # 默认假设标的可以卖到 0，也可以买到任意权重，后续再把不可平仓、停牌、无行情、涨跌停等约束逐步收紧到 lower / upper 上。
        upper = Series(inf, index=index, dtype=float)
        constraint_masks: Dict[DenialReason, Series] = {}

        # 不可平仓数量不能卖出，因此它对应的市值形成最低权重下界，例如当前持有 1000 股、只有 600 股可平，则剩余 400 股无论目标如何都必须保留。
        unclosable = (self._current_quantities - self._current_closable).clip(lower=0)
        lower = unclosable.mul(prices, fill_value=0) / self._total_value

        last, limit_up, limit_down = itemgetter('last', 'limit_up', 'limit_down')(self._prices)
        untradable = ~self._tradable

        # 停牌或无行情时无法买卖，目标权重只能等于当前权重，将上下界同时钉在 current_weights，后续求解器就不会对这些标的生成调仓量。
        lower[untradable] = current_weights[untradable]
        upper[untradable] = current_weights[untradable]

        limit_up_reached = self._tradable & reaches_limit_up_vectorized(last, limit_up, self._tick_sizes)
        limit_down_reached = self._tradable & reaches_limit_down_vectorized(last, limit_down, self._tick_sizes)
        if direction == POSITION_DIRECTION.LONG:
            # 多头调仓中，涨停限制买入，所以最高权重不能超过当前权重；
            # 跌停限制卖出，所以最低权重不能低于当前权重。
            upper[limit_up_reached] = upper[limit_up_reached].clip(upper=current_weights[limit_up_reached])
            lower[limit_down_reached] = lower[limit_down_reached].clip(lower=current_weights[limit_down_reached])
        else:
            # 空头方向的开平仓含义相反：跌停限制开空，涨停限制平空。
            upper[limit_down_reached] = upper[limit_down_reached].clip(upper=current_weights[limit_down_reached])
            lower[limit_up_reached] = lower[limit_up_reached].clip(lower=current_weights[limit_up_reached])

        # 这里先记录原始约束 mask；是否真的构成本次拒单，还要结合目标方向判断。
        # 例如多头下跌停只阻碍卖出，如果目标是增持，就不应被报告为 limit_down_sell。
        # 方向过滤在 _calc_adjusting_weights 中基于 desired_weights 与 current_weights 完成。
        constraint_masks[DenialReason.no_price] = self._no_price
        constraint_masks[DenialReason.closable_exceeded] = (lower > 0) & (self._current_closable == 0)
        if direction == POSITION_DIRECTION.LONG:
            constraint_masks[DenialReason.limit_up_buy] = limit_up_reached
            constraint_masks[DenialReason.limit_down_sell] = limit_down_reached
        else:
            constraint_masks[DenialReason.limit_down_buy] = limit_down_reached
            constraint_masks[DenialReason.limit_up_sell] = limit_up_reached
        return lower, upper, constraint_masks

    @staticmethod
    def _solve_bounded_scale(target_weights: Series, lower: Series, upper: Series, total_target_weight: float) -> float:
        """求解统一缩放系数，使约束后的目标权重尽量保持原组合比例。

        目标是找到 scale，使 sum(clip(target_weight * scale, lower, upper)) 接近目标总权重。
        这里不反复试探 scale，而是把每个正目标权重标的的 lower / upper 转换成 scale 事件点：
        lower / target_weight 表示该标的从下界固定状态进入随 scale 增长状态，
        upper / target_weight 表示该标的触达上界并重新变为固定状态。
        所有标的的事件点共同决定总权重函数的分段区间。
        """
        if total_target_weight <= lower.sum():
            return 0.0

        # 若所有资产都有有限上界，且目标总权重达到或超过上界总和，调用方可直接取各资产上界作为最接近的解。
        if isfinite(upper).all():
            upper_sum = upper.sum()
            if total_target_weight >= upper_sum:
                return inf

        # 两个相邻事件点之间，各标的状态不变：一部分固定在 lower/upper，合计为 fixed_sum；
        # 另一部分随 scale 增长，其原目标权重之和为 active_target。
        # 因此区间内总权重可写为 fixed_sum + active_target * scale。
        # 一旦目标总权重落入当前区间，就能直接解出 scale。
        active_target = 0.0
        fixed_sum = float(lower.sum())
        prev_scale = 0.0
        scale_breakpoints = []
        for order_book_id, weight in target_weights[target_weights > 0].items():
            weight = float(weight)
            lower_weight = float(lower[order_book_id])
            upper_weight = float(upper[order_book_id])
            start = lower_weight / weight
            scale_breakpoints.append((start, -lower_weight, weight))
            if isfinite(upper_weight):
                scale_breakpoints.append((upper_weight / weight, upper_weight, -weight))

        sorted_scale_breakpoints = sorted(scale_breakpoints)
        breakpoint_index = 0
        while breakpoint_index < len(sorted_scale_breakpoints):
            scale = sorted_scale_breakpoints[breakpoint_index][0]
            current_total = fixed_sum + active_target * prev_scale
            next_total = fixed_sum + active_target * scale
            if active_target > 0 and current_total <= total_target_weight <= next_total:
                return (total_target_weight - fixed_sum) / active_target

            while (
                breakpoint_index < len(sorted_scale_breakpoints)
                and sorted_scale_breakpoints[breakpoint_index][0] == scale
            ):
                _, fixed_delta, active_delta = sorted_scale_breakpoints[breakpoint_index]
                fixed_sum += fixed_delta
                active_target += active_delta
                breakpoint_index += 1
            prev_scale = scale

        if active_target > 0:
            return (total_target_weight - fixed_sum) / active_target
        return inf

    def _calc_adjusting_weights(self, direction: POSITION_DIRECTION) -> Tuple[Series, Dict[DenialReason, Series]]:
        """计算权重层面的调仓目标。

        该函数根据停牌、无行情、涨跌停、不可平仓等约束重新分配目标权重；
        实际下单数量、整手、最小下单量和现金约束由后续数量层流程处理。
        """
        prices = self._prices_settle_ccy
        total_target_weight = float(self._target_weights.sum())
        lower, upper, constraint_masks = self._calc_weight_bounds(direction, prices)
        current_weights = self._current_weights(prices)
        scale = self._solve_bounded_scale(self._target_weights, lower, upper, total_target_weight)
        # desired_weights 只用于判断原始调整方向，不作为最终目标权重下单。
        if scale == inf:
            # 目标总权重无法完全分配到可交易资产时，使用最接近的上界解。
            # 这里不把权重分给原始目标为 0 的资产，避免凭空引入新持仓。
            target_weights = lower.copy()
            positive_target = self._target_weights > 0
            target_weights[positive_target] = upper[positive_target]
            desired_weights = self._target_weights
        else:
            # 正常情况下先按统一 scale 保持原目标比例，再用上下界落实单票交易约束。
            # 被上下界锁住的权重差额，会在仍未触达上界且原目标权重大于 0 的标的之间按原比例分配。
            desired_weights = self._target_weights * scale
            target_weights = desired_weights.clip(lower=lower, upper=upper)

        denials: Dict[DenialReason, Series] = {}
        no_price = constraint_masks[DenialReason.no_price]
        denials[DenialReason.no_price] = no_price & (desired_weights != current_weights)
        denials[DenialReason.suspended_buy] = self._suspended & (desired_weights > current_weights)
        denials[DenialReason.suspended_sell] = self._suspended & (desired_weights < current_weights)
        denials[DenialReason.closable_exceeded] = constraint_masks[DenialReason.closable_exceeded] & (
            desired_weights < lower
        )

        # denials 只记录确实阻碍本次目标调整方向的约束。
        # 例如跌停标的若当前需要买入，它不应被标记为无法卖出。
        for reason, mask in constraint_masks.items():
            if reason in {DenialReason.no_price, DenialReason.closable_exceeded}:
                continue
            if reason in {DenialReason.limit_up_buy, DenialReason.limit_down_buy}:
                denials[reason] = mask & (desired_weights > current_weights)
            else:
                denials[reason] = mask & (desired_weights < current_weights)
        return target_weights, denials

    def _apply_cash_constraint(
        self, diff: Series, denials: Dict[DenialReason, Series], prices: Series, direction: POSITION_DIRECTION
    ) -> Series:
        """资金不足时按买入增量等比例收缩。

        现金约束依赖数量层确定后的 diff、交易成本和卖出回款，因此在权重和数量约束之后处理。
        这里保留卖出交易以释放资金，只缩减买入数量；该兜底主要处理交易成本、round、最小下单量等
        后置因素造成的小额现金偏差。此时重新整体压低目标仓位会同时减少本来可执行的卖出和买入，
        容易放大总仓位偏差；只缩减买入能保留已计算出的可执行调仓结果，通常误差更小。
        同时该方式只需一次向量化缩放和一次数量层复查，避免现金不足时反复进入权重求解和数量约束循环。
        """
        transaction_costs = self._estimate_transaction_costs(diff, prices)
        cash_consumed = (diff * prices).sum() + transaction_costs
        if cash_consumed <= self._cash_available:
            return diff

        buy_mask = diff > 0
        gross_buy_value = (diff[buy_mask] * prices[buy_mask]).sum()
        if gross_buy_value <= 0:
            return diff

        sell_proceeds = -(diff[diff < 0] * prices[diff < 0]).sum()
        buy_budget = max(float(self._cash_available + sell_proceeds - transaction_costs), 0.0)
        scaled_diff = diff.copy()
        scaled_diff[buy_mask] = (scaled_diff[buy_mask] * min(buy_budget / gross_buy_value, 1.0)).round(0)
        adjusted_quantities = self._current_quantities.add(scaled_diff, fill_value=0)
        cash_diff, cash_denials = self._calc_adjusting_quantities(adjusted_quantities, direction)
        for reason, mask in cash_denials.items():
            denials[reason] = denials.get(reason, Series(False, index=mask.index)) | mask
        return cash_diff

    def __call__(self, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG) -> AdjustingResult:
        """按交易约束计算可执行的目标组合调整量。

        算法核心思路：
        1. 将停牌、无行情、涨跌停、不可平仓等限制转换为单票权重上下界。
        2. 求解统一缩放系数，在约束内尽量保持原始目标权重比例。
        3. 将目标权重转换为调仓数量，并应用整手、最小下单量和现金约束。
        """
        if self._current_quantities.empty and self._target_weights.empty:
            return AdjustingResult(adjustments=Series(dtype='float64'), denials=dict())

        prices = self._prices_settle_ccy
        target_weights, denials = self._calc_adjusting_weights(direction)
        target_quantities = (self._total_value * target_weights / prices).round(0)
        # 权重层先用交易约束重新分配目标权重；数量层仍需在股数 round 后做最终交易约束校验。
        diff, round_denials = self._calc_adjusting_quantities(target_quantities, direction)
        for reason, mask in round_denials.items():
            denials[reason] = denials.get(reason, Series(False, index=mask.index)) | mask
        diff = self._apply_cash_constraint(diff, denials, prices, direction)
        return AdjustingResult(adjustments=diff, denials=self._format_denials(denials))


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
