from copy import copy

import numpy as np

from rqalpha.const import ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order, ALGO_ORDER_STYLES
from rqalpha.model.trade import Trade
from rqalpha.portfolio.account import Account
from rqalpha.environment import Environment
from rqalpha.utils import is_valid_price
from rqalpha.utils.price_limits import reaches_limit
from rqalpha.utils.i18n import gettext as _
from .base import DefaultMatcher
from ..slippage import SlippageDecider


class SignalMatcher(DefaultMatcher):
    def __init__(self, env: Environment, mod_config):
        self._env: Environment = env
        self._slippage_decider = SlippageDecider(mod_config.slippage_model, mod_config.slippage)
        self._price_limit = mod_config.price_limit
        self._partial_fill_on_insufficient_cash: bool = getattr(env.config.base, "partial_fill_on_insufficient_cash", False)

    def match(self, account: Account, order: Order, open_auction: bool):
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            return
        order_book_id = order.order_book_id
        instrument = self._env.data_proxy.get_active_instrument(order_book_id, self._env.trading_dt)
        price_board = self._env.price_board
        tick_size = self._env.data_proxy.get_tick_size(order_book_id)

        last_price = price_board.get_last_price(order_book_id)
        if not is_valid_price(last_price):
            listed_date = instrument.listed_date.date()
            if listed_date == self._env.trading_dt.date():
                reason = self._get_listed_date_cancelled_reason(order_book_id, listed_date)
            else:
                reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(order_book_id=order_book_id)
            order.mark_rejected(reason)
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
            return
        
        if order.type == ORDER_TYPE.LIMIT:
            deal_price = order.frozen_price
        elif isinstance(order.style, ALGO_ORDER_STYLES):
            deal_price, v = self._env.data_proxy.get_algo_bar(order.order_book_id, order.style, self._env.calendar_dt)
            if np.isnan(deal_price):
                reason = _(u"Order Cancelled: {order_book_id} bar no volume").format(order_book_id=order.order_book_id)
                order.mark_rejected(reason)
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
                return
        else:
            deal_price = last_price

        if self._price_limit:
            if reaches_limit(order_book_id, deal_price, order.side, price_board, tick_size):
                order.mark_rejected(_("Order Cancelled: current bar [{order_book_id}] reach the {limit_up_or_down} price.").format(
                    order_book_id=order.order_book_id, limit_up_or_down="limit_up" if order.side == SIDE.BUY else "limit_down",
                ))
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
                return
            
        trade_price = self._slippage_decider.get_trade_price(order, deal_price)
        should_cancel_remaining = False
        cash_cancel_reason = None
        if order.position_effect == POSITION_EFFECT.OPEN:
            fill, reason = self.resolve_open_fill(account, order, instrument, trade_price, order.quantity)
            if reason is not None:
                order.mark_rejected(reason)
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
                return
            should_cancel_remaining = fill < order.quantity
            if should_cancel_remaining:
                cash_cancel_reason = _(u"Order Cancelled: not enough money to fill {order_book_id}, fill {filled_volume} actually").format(
                    order_book_id=order.order_book_id, filled_volume=order.filled_quantity + fill
                )
        else:
            fill = order.quantity

        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction, order.position_effect)
        
        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=trade_price,
            amount=fill,
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=ct_amount
        )
        order.fill(trade)
        self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=copy(order)))

        if should_cancel_remaining:
            order.mark_cancelled(cash_cancel_reason)
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
            return

    def update(self, event):
        pass