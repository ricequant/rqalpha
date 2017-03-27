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

from collections import defaultdict

from rqalpha.const import ORDER_TYPE, SIDE, BAR_STATUS, MATCHING_TYPE
from rqalpha.environment import Environment
from rqalpha.events import EVENT, Event
from rqalpha.model.trade import Trade
from rqalpha.utils.i18n import gettext as _

from .decider import CommissionDecider, SlippageDecider, TaxDecider


class Matcher(object):
    def __init__(self, mod_config):
        if mod_config.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE:
            self._deal_price_decider = lambda bar: bar.close
        else:
            self._deal_price_decider = lambda bar: bar.open
        self._commission_decider = CommissionDecider(mod_config.commission_multiplier)
        self._slippage_decider = SlippageDecider(mod_config.slippage)
        self._tax_decider = TaxDecider()
        self._board = None
        self._turnover = defaultdict(int)
        self._calendar_dt = None
        self._trading_dt = None
        self._volume_percent = mod_config.volume_percent
        self._bar_limit = mod_config.bar_limit

    def update(self, calendar_dt, trading_dt, bar_dict):
        self._board = bar_dict
        self._turnover.clear()
        self._calendar_dt = calendar_dt
        self._trading_dt = trading_dt

    def match(self, open_orders):
        for account, order in open_orders:

            bar = self._board[order.order_book_id]
            bar_status = bar._bar_status

            if bar_status == BAR_STATUS.ERROR:
                listed_date = bar.instrument.listed_date.date()
                if listed_date == self._trading_dt.date():
                    reason = _(u"Order Cancelled: current security [{order_book_id}] can not be traded in listed date [{listed_date}]").format(
                        order_book_id=order.order_book_id,
                        listed_date=listed_date,
                    )
                else:
                    reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(
                        order_book_id=order.order_book_id)
                order.mark_rejected(reason)
                continue

            deal_price = self._deal_price_decider(bar)
            if order.type == ORDER_TYPE.LIMIT:
                if order.side == SIDE.BUY and order.price < deal_price:
                    continue
                if order.side == SIDE.SELL and order.price > deal_price:
                    continue
            else:
                if self._bar_limit and order.side == SIDE.BUY and bar_status == BAR_STATUS.LIMIT_UP:
                    reason = _(
                        "Order Cancelled: current bar [{order_book_id}] reach the limit_up price."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    continue
                elif self._bar_limit and order.side == SIDE.SELL and bar_status == BAR_STATUS.LIMIT_DOWN:
                    reason = _(
                        "Order Cancelled: current bar [{order_book_id}] reach the limit_down price."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    continue

            if self._bar_limit:
                if order.side == SIDE.BUY and bar_status == BAR_STATUS.LIMIT_UP:
                    continue
                if order.side == SIDE.SELL and bar_status == BAR_STATUS.LIMIT_DOWN:
                    continue

            volume_limit = round(bar.volume * self._volume_percent) - self._turnover[order.order_book_id]
            round_lot = bar.instrument.round_lot
            volume_limit = (volume_limit // round_lot) * round_lot
            if volume_limit <= 0:
                if order.type == ORDER_TYPE.MARKET:
                    reason = _('Order Cancelled: market order {order_book_id} volume {order_volume}'
                               ' due to volume limit').format(
                        order_book_id=order.order_book_id,
                        order_volume=order.quantity
                    )
                    order.mark_cancelled(reason)
                continue

            unfilled = order.unfilled_quantity
            fill = min(unfilled, volume_limit)
            ct_amount = account.positions.get_or_create(order.order_book_id).cal_close_today_amount(fill, order.side)
            price = self._slippage_decider.get_trade_price(order.side, deal_price)
            trade = Trade.__from_create__(
                order_id=order.order_id,
                calendar_dt=self._calendar_dt,
                trading_dt=self._trading_dt,
                price=price,
                amount=fill,
                side=order.side,
                position_effect=order.position_effect,
                order_book_id=order.order_book_id,
                frozen_price=order.frozen_price,
                close_today_amount=ct_amount
            )
            trade._commission = self._commission_decider.get_commission(account.type, trade)
            trade._tax = self._tax_decider.get_tax(account.type, trade)
            order.fill(trade)
            self._turnover[order.order_book_id] += fill

            Environment.get_instance().event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade))

            if order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
                reason = _(
                    "Order Cancelled: market order {order_book_id} volume {order_volume} is"
                    " larger than 25 percent of current bar volume, fill {filled_volume} actually"
                ).format(
                    order_book_id=order.order_book_id,
                    order_volume=order.quantity,
                    filled_volume=order.filled_quantity
                )
                order.mark_cancelled(reason)
