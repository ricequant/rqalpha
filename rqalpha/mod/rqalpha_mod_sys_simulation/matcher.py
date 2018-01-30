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

from rqalpha.utils import is_valid_price
from rqalpha.const import ORDER_TYPE, SIDE, MATCHING_TYPE
from rqalpha.events import EVENT, Event
from rqalpha.model.trade import Trade
from rqalpha.utils.i18n import gettext as _

from .decider import CommissionDecider, SlippageDecider, TaxDecider


class Matcher(object):
    def __init__(self, env, mod_config):
        self._commission_decider = CommissionDecider(mod_config.commission_multiplier)
        self._slippage_decider = SlippageDecider(mod_config.slippage)
        self._tax_decider = TaxDecider()
        self._turnover = defaultdict(int)
        self._calendar_dt = None
        self._trading_dt = None
        self._volume_percent = mod_config.volume_percent
        self._price_limit = mod_config.price_limit
        self._liquidity_limit = mod_config.liquidity_limit
        self._volume_limit = mod_config.volume_limit
        self._env = env
        self._deal_price_decider = self._create_deal_price_decider(mod_config.matching_type)

    def _create_deal_price_decider(self, matching_type):
        decider_dict = {
            MATCHING_TYPE.CURRENT_BAR_CLOSE: lambda order_book_id, side: self._env.bar_dict[order_book_id].close,
            MATCHING_TYPE.NEXT_BAR_OPEN: lambda order_book_id, side: self._env.bar_dict[order_book_id].open,
            MATCHING_TYPE.NEXT_TICK_LAST: lambda order_book_id, side: self._env.price_board.get_last_price(order_book_id),
            MATCHING_TYPE.NEXT_TICK_BEST_OWN: lambda order_book_id, side: self._best_own_price_decider(order_book_id, side),
            MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY: lambda order_book_id, side: (
                self._env.price_board.get_a1(order_book_id) if side == SIDE.BUY else self._env.price_board.get_b1(order_book_id))
        }
        return decider_dict[matching_type]

    def _best_own_price_decider(self, order_book_id, side):
        price = self._env.price_board.get_b1(order_book_id) if side == SIDE.BUY else self._env.price_board.get_a1(order_book_id)
        if price == 0:
            price = self._env.price_board.get_last_price(order_book_id)
        return price

    def update(self, calendar_dt, trading_dt):
        self._turnover.clear()
        self._calendar_dt = calendar_dt
        self._trading_dt = trading_dt

    def match(self, open_orders):
        price_board = self._env.price_board
        for account, order in open_orders:
            order_book_id = order.order_book_id
            instrument = self._env.get_instrument(order_book_id)

            if not is_valid_price(price_board.get_last_price(order_book_id)):
                listed_date = instrument.listed_date.date()
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

            deal_price = self._deal_price_decider(order_book_id, order.side)
            if order.type == ORDER_TYPE.LIMIT:
                if order.side == SIDE.BUY and order.price < deal_price:
                    continue
                if order.side == SIDE.SELL and order.price > deal_price:
                    continue
                # 是否限制涨跌停不成交
                if self._price_limit:
                    if order.side == SIDE.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                        continue
                    if order.side == SIDE.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                        continue
                if self._liquidity_limit:
                    if order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0:
                        continue
                    if order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0:
                        continue
            else:
                if self._price_limit:
                    if order.side == SIDE.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                        reason = _(
                            "Order Cancelled: current bar [{order_book_id}] reach the limit_up price."
                        ).format(order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                    if order.side == SIDE.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                        reason = _(
                            "Order Cancelled: current bar [{order_book_id}] reach the limit_down price."
                        ).format(order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                if self._liquidity_limit:
                    if order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0:
                        reason = _(
                            "Order Cancelled: [{order_book_id}] has no liquidity."
                        ).format(order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                    if order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0:
                        reason = _(
                            "Order Cancelled: [{order_book_id}] has no liquidity."
                        ).format(order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue

            if self._volume_limit:
                bar = self._env.bar_dict[order_book_id]
                volume_limit = round(bar.volume * self._volume_percent) - self._turnover[order.order_book_id]
                round_lot = instrument.round_lot
                volume_limit = (volume_limit // round_lot) * round_lot
                if volume_limit <= 0:
                    if order.type == ORDER_TYPE.MARKET:
                        reason = _(u"Order Cancelled: market order {order_book_id} volume {order_volume}"
                                   u" due to volume limit").format(
                            order_book_id=order.order_book_id,
                            order_volume=order.quantity
                        )
                        order.mark_cancelled(reason)
                    continue

                unfilled = order.unfilled_quantity
                fill = min(unfilled, volume_limit)
            else:
                fill = order.unfilled_quantity

            ct_amount = account.positions.get_or_create(order.order_book_id).cal_close_today_amount(fill, order.side)
            price = self._slippage_decider.get_trade_price(order.side, deal_price)
            trade = Trade.__from_create__(
                order_id=order.order_id,
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

            self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))

            if order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
                reason = _(
                    u"Order Cancelled: market order {order_book_id} volume {order_volume} is"
                    u" larger than {volume_percent_limit} percent of current bar volume, fill {filled_volume} actually"
                ).format(
                    order_book_id=order.order_book_id,
                    order_volume=order.quantity,
                    filled_volume=order.filled_quantity,
                    volume_percent_limit=self._volume_percent * 100.0
                )
                order.mark_cancelled(reason)
