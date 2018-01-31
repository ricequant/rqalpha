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

import six

from rqalpha.model.base_account import BaseAccount
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, SIDE, POSITION_DIRECTION
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log, system_log
from rqalpha.interface import AbstractAccount
from rqalpha.utils.repr import property_repr

from .booking_position import BookingPosition, BookingPositions


class BookingAccount(object):

    NaN = float('NaN')

    __repr__ = property_repr

    def __init__(self, backward_trade_set=None, register_event=True):
        self._positions_dict = {
            POSITION_DIRECTION.LONG: BookingPositions(POSITION_DIRECTION.LONG),
            POSITION_DIRECTION.SHORT: BookingPositions(POSITION_DIRECTION.SHORT),
        }
        self._backward_trade_set = backward_trade_set if backward_trade_set is not None else set()

        if register_event:
            self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        event_bus.add_listener(EVENT.SETTLEMENT, self._settlement)

    def fast_forward(self, orders, trades=list()):
        for trade in trades:
            if trade.exec_id in self._backward_trade_set:
                continue
            self._apply_trade(trade)

    def _get_direction(self, side, position_effect):
        direction = None
        if position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY):
            if side == SIDE.BUY:
                direction = POSITION_DIRECTION.SHORT
            elif side == SIDE.SELL:
                direction = POSITION_DIRECTION.LONG
        elif position_effect == POSITION_EFFECT.OPEN:
            if side == SIDE.BUY:
                direction = POSITION_DIRECTION.LONG
            elif side == SIDE.SELL:
                direction = POSITION_DIRECTION.SHORT
        return direction

    def get_position(self, order_book_id, direction, booking=None):
        return self._positions_dict[direction].get_or_create(order_book_id)

    def get_positions(self, booking=None):
        total_positions = []
        for direction, positions in self._positions_dict.items():
            for order_book_id, position in positions.items():
                if position.quantity != 0:
                    total_positions.append(position)
        return total_positions

    def _settlement(self, event, check_delist=True):
        delete_list = []
        for direction, positions in list(self._positions_dict.items()):
            for order_book_id, position in list(positions.items()):
                pass

        for direction, positions in self._positions_dict.items():
            for order_book_id, position in positions.items():
                if check_delist and position.is_de_listed() and position.quantity != 0:
                    user_system_log.warn(
                        _(u"{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                    delete_list.append((order_book_id, direction))
                    # del self._positions[order_book_id]
                elif position.quantity == 0:
                    delete_list.append((order_book_id, direction))
                    # del self._positions[order_book_id]
                else:
                    position.apply_settlement()

        for order_book_id, direction in delete_list:
            self._positions_dict[direction].pop(order_book_id)

        self._backward_trade_set.clear()

    def _on_trade(self, event):
        trade = event.trade
        self._apply_trade(trade)

    def _apply_trade(self, trade):
        if trade.exec_id in self._backward_trade_set:
            return

        order_book_id = trade.order_book_id

        if trade.side not in (SIDE.BUY, SIDE.SELL):
            raise RuntimeError("unknown side, trade {}".format(trade))

        long_positions = self._positions_dict[POSITION_DIRECTION.LONG]
        short_positions = self._positions_dict[POSITION_DIRECTION.SHORT]

        if trade.position_effect == POSITION_EFFECT.OPEN:
            if trade.side == SIDE.BUY:
                position = long_positions.get_or_create(order_book_id)
            elif trade.side == SIDE.SELL:
                position = short_positions.get_or_create(order_book_id)
        elif trade.position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY):
            if trade.side == SIDE.BUY:
                position = short_positions.get_or_create(order_book_id)
            elif trade.side == SIDE.SELL:
                position = long_positions.get_or_create(order_book_id)
        else:
            # NOTE: 股票如果没有position_effect就特殊处理
            position = long_positions.get_or_create(order_book_id)

        position.apply_trade(trade)

        self._backward_trade_set.add(trade.exec_id)

    @property
    def cash(self):
        return 0

    @property
    def positions(self):
        return {}

    @property
    def total_value(self):
        return 0

    @property
    def type(self):
        return "BookingAccount"

    @property
    def frozen_cash(self):
        return 0

    @property
    def market_value(self):
        return 0

    @property
    def transaction_cost(self):
        return 0
