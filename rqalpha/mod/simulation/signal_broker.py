# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha.interface import AbstractBroker
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.events import EVENT, Event
from rqalpha.execution_context import ExecutionContext
from rqalpha.model.order import LimitOrder
from rqalpha.model.trade import Trade
from rqalpha.const import BAR_STATUS, SIDE
from rqalpha.environment import Environment

from .decider import CommissionDecider, SlippageDecider, TaxDecider
from .utils import init_portfolio


class SignalBroker(AbstractBroker):
    def __init__(self, env, mod_config):
        self._env = env
        self._commission_decider = CommissionDecider(mod_config.commission_multiplier)
        self._slippage_decider = SlippageDecider(mod_config.slppage)
        self._tax_decider = TaxDecider()
        self._portfolio = None

    def get_portfolio(self):
        if self._portfolio is None:
            self._portfolio = init_portfolio(self._env)
        return self._portfolio

    def get_open_orders(self):
        return []

    def submit_order(self, order):
        account = ExecutionContext.get_account(order)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        account.append_order(order)
        if order._is_final():
            return
        order._active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
        self._match(account, order)

    def cancel_order(self, order):
        user_system_log.error(_("cancel_order function is not supported in signal mode"))
        return None

    def _match(self, account, order):
        bar_dict = ExecutionContext.get_current_bar_dict()
        # TODO support tick cal
        bar = bar_dict[order.order_book_id]

        bar_status = bar._bar_status

        if bar_status == BAR_STATUS.ERROR:
            listed_date = bar.instrument.listed_date.date()
            if listed_date == self._trading_dt.date():
                reason = _(
                    "Order Cancelled: current security [{order_book_id}] can not be traded in listed date [{listed_date}]").format(
                    order_book_id=order.order_book_id,
                    listed_date=listed_date,
                )
            else:
                reason = _("Order Cancelled: current bar [{order_book_id}] miss market data.").format(
                    order_book_id=order.order_book_id)
            order._mark_rejected(reason)
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
            return

        if isinstance(order.style, LimitOrder):
            deal_price = order.style.get_limit_price()
        else:
            deal_price = bar.close

        deal_price = min(deal_price, bar.high)
        deal_price = max(deal_price, bar.low)

        deal_price = self._slippage_decider.get_trade_price(order.side, deal_price)

        if (order.side == SIDE.BUY and bar_status == BAR_STATUS.LIMIT_UP) or (
                order.side == SIDE.SELL and bar_status == BAR_STATUS.LIMIT_DOWN):
            user_system_log.warning(_("You have traded {order_book_id} with {quantity} lots in {bar_status}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                bar_status=bar_status
            ))
        ct_amount = account.portfolio.positions[order.order_book_id]._cal_close_today_amount(order.quantity, order.side)
        trade = Trade.__from_create__(order=order, calendar_dt=ExecutionContext.get_current_calendar_dt(),
                                      trading_dt=ExecutionContext.get_current_trading_dt(), price=deal_price,
                                      amount=order.quantity, close_today_amount=ct_amount)
        trade._commission = self._commission_decider.get_commission(account.type, trade)
        trade._tax = self._tax_decider.get_tax(account.type, trade)
        order._fill(trade)

        Environment.get_instance().event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade))
