import datetime
from collections import defaultdict
from typing import Optional, NamedTuple

from rqalpha.const import ORDER_TYPE, SIDE, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.account import Account
from rqalpha.utils.price_limits import reaches_limit
from rqalpha.interface import TransactionCostArgs, TransactionCost
from rqalpha.utils import is_valid_price
from rqalpha.utils.i18n import gettext as _
from ..slippage import SlippageDecider


class MatchFillResult(NamedTuple):
    quantity: int
    cancel_reason: Optional[str] = None


class AbstractMatcher:
    def match(self, account: Account, order: Order, open_auction: bool) -> None:
        raise NotImplementedError

    def update(self, event):
        raise NotImplementedError


class BaseMatcher(AbstractMatcher):
    def __init__(self, env: Environment, mod_config, partial_fill_on_insufficient_cash: bool = False):
        self._env: Environment = env
        self._slippage_decider = SlippageDecider(mod_config.slippage_model, mod_config.slippage)
        self._price_limit = mod_config.price_limit
        self._partial_fill_on_insufficient_cash: bool = partial_fill_on_insufficient_cash
        self._turnover = defaultdict(int)
        self._volume_percent = mod_config.volume_percent
        self._inactive_limit = mod_config.inactive_limit
        self._volume_limit = mod_config.volume_limit

    def _reject_order(self, account: Account, order: Order, reason: str):
        order.mark_rejected(reason)

    def _cancel_order(self, account: Account, order: Order, reason: str):
        order.mark_cancelled(reason)

    def _get_deal_price(self, order: Order, open_auction: bool) -> float:
        raise NotImplementedError

    def _handle_invalid_price_order(self, instrument: Instrument, order: Order, account: Account):
        raise NotImplementedError

    def _reject_order_of_listed_date(self, order: Order, listed_date: datetime.date, account: Account):
        reason = _(u"Order Cancelled: current security [{order_book_id}] can not be traded in listed date [{listed_date}]").format(
            order_book_id=order.order_book_id, listed_date=listed_date
        )
        self._reject_order(account, order, reason)

    def _can_match_limit_order(
        self, order: Order, deal_price: float, tick_size: float, account: Account, open_auction: bool = False
    ) -> bool:
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
                    self._reject_order(account, order, reason)
                    return False
        return True

    def _during_call_auction(self, instrument: Instrument, open_auction: bool) -> bool:
        # 判断订单是否是在 open_auction 时间段
        if self._env.config.base.frequency == "tick":
            # tick 策略没有 open_auction，因此需要通过 calendat_dt 来判断是否处于 open_auction
            return instrument.during_call_auction(self._env.calendar_dt)
        return open_auction

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> MatchFillResult:
        # 在当前 bar/tick/盘口流动性下，获取可撮合的最大数量
        raise NotImplementedError

    def _get_trade_price(self, order: Order, deal_price: float, open_auction: bool) -> float:
        if open_auction:
            return deal_price
        return self._slippage_decider.get_trade_price(order, deal_price)

    def _calc_required_cash(self, order: Order, instrument: Instrument, price: float, fill: int):
        transaction_cost: TransactionCost = self._env.calc_transaction_cost(
            TransactionCostArgs(instrument, price, fill, order.side, order.position_effect)
        )
        cash_occupation = instrument.calc_cash_occupation(price, fill, order.position_direction, order.trading_datetime.date())
        return cash_occupation + transaction_cost.total

    def _resolve_open_fill(self, account: Account, order: Order, instrument: Instrument, price: float, fill: int) -> MatchFillResult:
        available_cash = account.cash + order.init_frozen_cash

        if not self._partial_fill_on_insufficient_cash:
            if self._slippage_decider.decider.rate != 0:
                # 标的价格经过滑点处理后，账户资金可能不够买入，需要进行验证
                required_cash = self._calc_required_cash(order, instrument, price, order.quantity)
                if required_cash > available_cash:
                    status_label = "Cancelled" if order.filled_quantity != 0 else "Rejected"
                    reason = _(u"Order {status_label}: not enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                                status_label=status_label, order_book_id=instrument.order_book_id, cost_money=required_cash, cash = available_cash
                                )
                    return MatchFillResult(fill, reason)
            return MatchFillResult(fill)

        else:
            min_quantity = instrument.min_order_quantity
            step = instrument.order_step_size
            if fill >= min_quantity and (fill - min_quantity) % step == 0:
                required_cash = self._calc_required_cash(order, instrument, price, fill)
                if required_cash <= available_cash:
                    return MatchFillResult(fill)

            cash_fill = 0
            low = 0
            high = (fill - min_quantity) // step
            while low <= high:
                mid = (low + high) // 2
                candidate_fill = min_quantity + mid * step
                required_cash = self._calc_required_cash(order, instrument, price, candidate_fill)
                if required_cash <= available_cash:
                    cash_fill = candidate_fill
                    low = mid + 1
                else:
                    high = mid - 1

            if cash_fill > 0:
                return MatchFillResult(cash_fill)

            min_required_cash = self._calc_required_cash(order, instrument, price, min_quantity)
            status_label = "Cancelled" if order.filled_quantity != 0 else "Rejected"
            reason = _(u"Order {status_label}: not enough money to buy one lot of {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                status_label=status_label, order_book_id=order.order_book_id, cost_money=min_required_cash, cash=available_cash
            )

        return MatchFillResult(0, reason)

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

    def _after_trade(self, account: Account, order: Order, open_auction: bool, cash_cancel_reason: Optional[str] = None):
        if cash_cancel_reason is not None:
            self._cancel_order(account, order, cash_cancel_reason)
            return
        elif order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
            frequency = "tick" if self._env.config.base.frequency == "tick" else "bar"
            reason = _(
                u"Order Cancelled: market order {order_book_id} volume {order_volume} is"
                u" larger than {volume_percent_limit} percent of current {frequency} volume, fill {filled_volume} actually"
            ).format(
                order_book_id=order.order_book_id,
                order_volume=order.quantity,
                filled_volume=order.filled_quantity,
                frequency=frequency,
                volume_percent_limit=self._volume_percent * 100.0
            )
            self._cancel_order(account, order, reason)
            return

    def match(self, account: Account, order: Order, open_auction: bool) -> None:
        # 标的信息
        order_book_id = order.order_book_id
        instrument = self._env.data_proxy.get_active_instrument(order_book_id, self._env.trading_dt)
        tick_size = self._env.data_proxy.get_tick_size(order_book_id)

        open_auction = self._during_call_auction(instrument, open_auction)

        deal_price = self._get_deal_price(order, open_auction)
        if not is_valid_price(deal_price):
            self._handle_invalid_price_order(instrument, order, account)
            return

        if not self._can_match_limit_order(order, deal_price, tick_size, account, open_auction):
            return

        match_fill_result = self._get_liquidity_limited_fill(order, instrument, open_auction)
        if match_fill_result.cancel_reason is not None:
            self._cancel_order(account, order, match_fill_result.cancel_reason)
            return
        fill = match_fill_result.quantity
        if fill == 0:
            return

        # 获取经过滑点处理后的成交价格
        price = self._get_trade_price(order, deal_price, open_auction)

        cash_cancel_reason = None
        if order.position_effect == POSITION_EFFECT.OPEN:
            match_fill_result = self._resolve_open_fill(
                account=account, order=order, instrument=instrument, price=price, fill=fill
            )
            if match_fill_result.cancel_reason is not None:
                if order.filled_quantity != 0:  # 如果存在前一档已生成 trade，后一档因为现金不足的情况时，应该是取消订单而非拒单
                    self._cancel_order(account, order, match_fill_result.cancel_reason)
                else:
                    self._reject_order(account, order, match_fill_result.cancel_reason)
                return
            if match_fill_result.quantity < fill:
                cash_cancel_reason = _(u"Order Cancelled: not enough money to fill {order_book_id}, fill {filled_volume} actually").format(
                    order_book_id=order.order_book_id, filled_volume=order.filled_quantity + match_fill_result.quantity
                )
            fill = match_fill_result.quantity

        # 平今的数量
        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction, order.position_effect)

        self._publish_trade(account, order, price, fill, open_auction, ct_amount)
        self._after_trade(account, order, open_auction, cash_cancel_reason)
