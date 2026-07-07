from copy import copy
from typing import Optional

from rqalpha.const import ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order, ALGO_ORDER_STYLES
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.account import Account
from rqalpha.utils import is_valid_price
from rqalpha.utils.price_limits import reaches_limit
from rqalpha.utils.i18n import gettext as _
from .base import BaseMatcher, MatchFillResult


class SignalMatcher(BaseMatcher):
    def _reject_order(self, account, order, reason):
        super()._reject_order(account, order, reason)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))

    def _cancel_order(self, account, order, reason):
        super()._cancel_order(account, order, reason)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))

    def _get_deal_price(self, order, open_auction):
        last_price = self._env.price_board.get_last_price(order.order_book_id)
        if not is_valid_price(last_price):
            return last_price
        if order.type == ORDER_TYPE.LIMIT:
            return order.frozen_price
        elif isinstance(order.style, ALGO_ORDER_STYLES):
            deal_price, _ = self._env.data_proxy.get_algo_bar(order.order_book_id, order.style, self._env.calendar_dt)
            return deal_price
        return last_price

    def _handle_invalid_price_order(self, instrument: Instrument, order: Order, account: Account):
        # 信号模式下的无效价格分两种情况：
        # 1.last_price 为无效价格，该情况下需要判断是否为 listed_date 当天
        # 2.algo_order 情况下由于没有成交量导致的无效价格
        if not is_valid_price(self._env.price_board.get_last_price(order.order_book_id)):
            listed_date = instrument.listed_date.date()
            if listed_date == self._env.trading_dt.date():
                self._reject_order_of_listed_date(order, listed_date, account)
            else:
                reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(order_book_id=order.order_book_id)
                self._reject_order(account, order, reason)
        else:
            reason = _(u"Order Cancelled: {order_book_id} bar no volume").format(order_book_id=order.order_book_id)
            self._reject_order(account, order, reason)

    def _can_match_limit_order(self, order: Order, deal_price: float, tick_size: float, account: Account, open_auction: bool = False):
        if self._price_limit:
            if reaches_limit(order.order_book_id, deal_price, order.side, self._env.price_board, tick_size):
                reason = _("Order Cancelled: current bar [{order_book_id}] reach the {limit_up_or_down} price.").format(
                    order_book_id=order.order_book_id, limit_up_or_down="limit_up" if order.side == SIDE.BUY else "limit_down",
                )
                self._reject_order(account, order, reason)
                return False
        return True

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> MatchFillResult:
        return MatchFillResult(quantity=order.quantity)

    def _get_trade_price(self, order, deal_price, open_auction):
        return self._slippage_decider.get_trade_price(order, deal_price)

    def _after_trade(self, account: Account, order: Order, open_auction: bool, cash_cancel_reason: Optional[str] = None):
        if cash_cancel_reason is not None:
            self._cancel_order(account, order, cash_cancel_reason)
            return

    def match(self, account: Account, order: Order, open_auction: bool):
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            return
        super().match(account, order, open_auction)

    def update(self, event):
        pass
