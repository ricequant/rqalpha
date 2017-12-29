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
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, SIDE
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
from rqalpha.interface import AbstractAccount
from rqalpha.utils.repr import property_repr


class BookingAccount(AbstractAccount):

    NaN = float('NaN')

    __repr__ = property_repr

    def __init__(self, positions, backward_trade_set=None, register_event=True):
        self._positions = positions
        self._backward_trade_set = backward_trade_set if backward_trade_set is not None else set()
        if register_event:
            self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.SETTLEMENT, self._settlement)

    def fast_forward(self, orders, trades=list()):
        for trade in trades:
            if trade.exec_id in self._backward_trade_set:
                continue
            self._apply_trade(trade)

    def order(self, order_book_id, quantity, style, target=False):
        """
        [Required]

        系统下单函数会调用该函数来完成下单操作
        """
        raise NotImplementedError

    def get_state(self):
        return {}

    def set_state(self, state):
        pass

    @property
    def type(self):
        return "BookingAccount"

    @property
    def positions(self):
        return self._positions

    @property
    def frozen_cash(self):
        return 0

    @property
    def cash(self):
        return 0

    @property
    def market_value(self):
        raise NotImplementedError

    @property
    def transaction_cost(self):
        return 0

    def _on_order_pending_new(self, event):
        if self != event.account:
            return

    def _on_order_unsolicited_update(self, event):
        if self != event.account:
            return

    def _on_trade(self, event):
        if self != event.account:
            return
        self._apply_trade(event.trade)

    def _apply_trade(self, trade):
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        position = self._positions.get_or_create(order_book_id)
        position.apply_trade(trade)

        self._backward_trade_set.add(trade.exec_id)
