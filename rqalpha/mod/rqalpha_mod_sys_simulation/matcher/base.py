import datetime
from collections import defaultdict
from typing import Optional

from rqalpha.const import ORDER_TYPE, SIDE, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.account import Account
from rqalpha.utils.price_limits import reaches_limit
from rqalpha.interface import TransactionCostArgs, TransactionCost
from rqalpha.utils.i18n import gettext as _
from ..slippage import SlippageDecider


class AbstractMatcher:
    def match(self, account: Account, order: Order, open_auction: bool) -> None:
        raise NotImplementedError

    def update(self, event):
        raise NotImplementedError


class BaseMatcher(AbstractMatcher):
    """
    撮合主流程：
    1. 获取订单成交价。
    2. 校验限价条件和涨跌停规则。
    3. 依据当前 bar、tick 或盘口流动性确定最大可成交量。
    4. 对开仓订单，依据可用资金确定实际成交量。
    5. 计算平今数量。
    6. 生成 Trade 并发布成交事件。
    7. 处理未完全成交的剩余订单。
    """
    def __init__(self, env: Environment, mod_config, partial_fill_on_insufficient_cash: bool = False):
        self._env: Environment = env
        self._slippage_decider = SlippageDecider(mod_config.slippage_model, mod_config.slippage)
        self._price_limit = mod_config.price_limit
        self._partial_fill_on_insufficient_cash: bool = partial_fill_on_insufficient_cash
        self._turnover = defaultdict(int)
        self._volume_percent = mod_config.volume_percent
        self._inactive_limit = mod_config.inactive_limit
        self._volume_limit = mod_config.volume_limit

    def _get_deal_price(self, order: Order, instrument: Instrument, open_auction: bool) -> Optional[float]:
        """
        获取订单成交价。
        返回合法成交价；无法获取时，子类可按场景更新订单状态，并返回 None。
        """
        raise NotImplementedError

    def _reject_order_of_listed_date(self, order: Order, listed_date: datetime.date):
        reason = _(u"Order Cancelled: current security [{order_book_id}] can not be traded in listed date [{listed_date}]").format(
            order_book_id=order.order_book_id, listed_date=listed_date
        )
        order.mark_rejected(reason)

    def _can_match_limit_order(
        self, order: Order, deal_price: float, tick_size: float, account: Account, open_auction: bool = False
    ) -> bool:
        """
        校验订单是否满足当前成交价、限价和涨跌停规则。
        不能撮合时返回 False。限价单保持当前状态；市价或算法单触及涨跌停时标记为拒单。
        """
        price_board = self._env.price_board
        if order.type == ORDER_TYPE.LIMIT:
            if order.side == SIDE.BUY and order.price < deal_price:
                return False
            if order.side == SIDE.SELL and order.price > deal_price:
                return False
            # 是否限制涨跌停不成交
            if self._price_limit:
                if reaches_limit(order.order_book_id, deal_price, order.side, price_board, tick_size):
                    return False
        else:
            if self._price_limit:
                if reaches_limit(order.order_book_id, deal_price, order.side, price_board, tick_size):
                    reason = _(
                        "Order Cancelled: current {frequency} [{order_book_id}] reach the {limit_up_or_down} price."
                    ).format(
                        frequency="tick" if self._env.config.base.frequency == "tick" else "bar",
                        order_book_id=order.order_book_id,
                        limit_up_or_down="limit_up" if order.side == SIDE.BUY else "limit_down")
                    order.mark_rejected(reason)
                    return False
        return True

    def _during_call_auction(self, instrument: Instrument, open_auction: bool) -> bool:
        """
        判断当前撮合是否处于集合竞价时段。
        tick 模式依据 calendar_dt 判断；其他频率使用 broker 传入的 open_auction 标记。
        """
        if self._env.config.base.frequency == "tick":
            # tick 策略没有 open_auction，因此需要通过 calendat_dt 来判断是否处于 open_auction
            return instrument.during_call_auction(self._env.calendar_dt)
        return open_auction

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> Optional[int]:
        """
        返回当前 bar、tick 或盘口流动性下的最大可成交量。
        没有可成交数量时返回 None；子类可按场景更新订单状态。
        """
        raise NotImplementedError

    def _get_execution_price(self, order: Order, deal_price: float, open_auction: bool) -> float:
        """
        返回用于创建 Trade 的最终成交价。
        集合竞价直接使用 deal_price；其他时段默认经滑点模型调整，子类可覆盖。
        """
        if open_auction:
            return deal_price
        return self._slippage_decider.get_trade_price(order, deal_price)

    def _resolve_open_fill(self, account: Account, order: Order, instrument: Instrument, price: float, fill: int) -> Optional[int]:
        """
        根据执行价和可用资金（含本订单冻结资金）确定开仓订单的实际成交量。
        - 未启用部分成交时，仅在非零滑点下重新校验完整订单所需资金；不足则拒单或取消并返回 None。
        - 启用部分成交时，返回不超过 fill 的最大合法下单数量；不足一手时拒单或取消并返回 None。
        """

        def _calc_required_cash(order: Order, instrument: Instrument, price: float, fill: int):
            transaction_cost: TransactionCost = self._env.calc_transaction_cost(
                TransactionCostArgs(instrument, price, fill, order.side, order.position_effect)
            )
            cash_occupation = instrument.calc_cash_occupation(
                price, fill, order.position_direction, order.trading_datetime.date()
            )
            return cash_occupation + transaction_cost.total

        available_cash = account.cash + order.init_frozen_cash

        if not self._partial_fill_on_insufficient_cash:
            if self._slippage_decider.decider.rate != 0:
                # 执行价经滑点调整后，账户资金可能不足，需要重新校验。
                required_cash = _calc_required_cash(order, instrument, price, order.quantity)
                if required_cash > available_cash:
                    status_label = "Cancelled" if order.filled_quantity != 0 else "Rejected"
                    reason = _(u"Order {status_label}: not enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                                status_label=status_label, order_book_id=instrument.order_book_id, cost_money=required_cash, cash = available_cash
                                )
                    if status_label == "Cancelled":
                        order.mark_cancelled(reason)
                    else:
                        order.mark_rejected(reason)
                    return None
            return fill

        else:
            min_quantity = instrument.min_order_quantity
            step = instrument.order_step_size
            if fill >= min_quantity and (fill - min_quantity) % step == 0:
                required_cash = _calc_required_cash(order, instrument, price, fill)
                if required_cash <= available_cash:
                    return fill

            cash_fill = 0
            low = 0
            high = (fill - min_quantity) // step
            while low <= high:
                mid = (low + high) // 2
                candidate_fill = min_quantity + mid * step
                required_cash = _calc_required_cash(order, instrument, price, candidate_fill)
                if required_cash <= available_cash:
                    cash_fill = candidate_fill
                    low = mid + 1
                else:
                    high = mid - 1

            if cash_fill > 0:
                return cash_fill

            min_required_cash = _calc_required_cash(order, instrument, price, min_quantity)
            # 已有成交时，后续因资金不足终止撮合应取消剩余订单。
            status_label = "Cancelled" if order.filled_quantity != 0 else "Rejected"
            reason = _(u"Order {status_label}: not enough money to buy one lot of {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                status_label=status_label, order_book_id=order.order_book_id, cost_money=min_required_cash, cash=available_cash
            )
            if status_label == "Cancelled":
                order.mark_cancelled(reason)
            else:
                order.mark_rejected(reason)

            return None

    def _publish_trade(self, account: Account, order: Order, price: float, amount: int, open_auction: bool, close_today_amount: int):
        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=price,
            amount=amount,
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order.order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=close_today_amount
        )
        order.fill(trade)
        self._turnover[order.order_book_id] += amount
        self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))

    def _handle_unfilled_order(self, account: Account, order: Order, open_auction: bool):
        """
        处理一轮撮合后仍有未成交数量的订单。
        子类可取消市价单、保留限价单，或继续逐档撮合。
        """
        raise NotImplementedError

    def match(self, account: Account, order: Order, open_auction: bool) -> None:
        # 读取合约与报价规则
        order_book_id = order.order_book_id
        instrument = self._env.data_proxy.get_active_instrument(order_book_id, self._env.trading_dt)
        tick_size = self._env.data_proxy.get_tick_size(order_book_id)

        open_auction = self._during_call_auction(instrument, open_auction)

        # 1. 获取订单成交价
        deal_price = self._get_deal_price(order, instrument, open_auction)
        if deal_price is None:
            return
        # 2. 校验限价条件和涨跌停规则
        if not self._can_match_limit_order(order, deal_price, tick_size, account, open_auction):
            return
        # 3. 获取在当前流动性下订单的最大可成交量
        fill = self._get_liquidity_limited_fill(order, instrument, open_auction)
        if fill is None:
            return

        price = self._get_execution_price(order, deal_price, open_auction)
        cash_cancel_reason = None
        # 4. 对开仓订单，依据可用资金确定实际成交量
        if order.position_effect == POSITION_EFFECT.OPEN:
            open_fill = self._resolve_open_fill(account=account, order=order, instrument=instrument, price=price, fill=fill)
            if open_fill is None:
                return
            if open_fill < fill:
                cash_cancel_reason = _(u"Order Cancelled: not enough money to fill {order_book_id}, fill {filled_volume} actually").format(
                    order_book_id=order.order_book_id, filled_volume=order.filled_quantity + open_fill
                )
            fill = open_fill

        # 5. 计算平今数量
        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction, order.position_effect)

        # 6. 生成 Trade 并发布成交事件
        self._publish_trade(account, order, price, fill, open_auction, ct_amount)

        # 7. 处理未完全成交的剩余订单
        if cash_cancel_reason is not None:
            order.mark_cancelled(cash_cancel_reason)
            return
        if order.unfilled_quantity != 0:
            self._handle_unfilled_order(account, order, open_auction)
