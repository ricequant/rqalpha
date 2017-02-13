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
import time

from ..utils import id_gen
from ..utils.repr import property_repr, properties

TradePersistMap = {
    "_calendar_dt": "_calendar_dt",
    "_trading_dt": "_trading_dt",
    "_price": "_price",
    "_amount": "_amount",
    "_order_id": "_order_id",
    "_commission": "_commission",
    "_tax": "_tax",
    "_trade_id": "_trade_id",
    "_close_today_amount": "_close_today_amount",
}


class Trade(object):
    __slots__ = ["_calendar_dt", "_trading_dt", "_price", "_amount", "_order", "_commission", "_tax", "_trade_id",
                 "_close_today_amount"]

    __repr__ = property_repr

    trade_id_gen = id_gen(int(time.time()))

    def __init__(self):
        self._calendar_dt = None
        self._trading_dt = None
        self._price = None
        self._amount = None
        self._order = None
        self._commission = None
        self._tax = None
        self._trade_id = None
        self._close_today_amount = None

    @classmethod
    def __from_create__(cls, order, calendar_dt, trading_dt, price, amount, commission=0., tax=0., trade_id=None,
                        close_today_amount=0):
        trade = cls()
        trade._calendar_dt = calendar_dt
        trade._trading_dt = trading_dt
        trade._price = price
        trade._amount = amount
        trade._order = order
        trade._commission = commission
        trade._tax = tax
        trade._trade_id = trade_id if trade_id is not None else next(trade.trade_id_gen)
        trade._close_today_amount = close_today_amount
        return trade

    @classmethod
    def __from_dict__(cls, trade_dict, order):
        trade = cls()
        for persist_key, origin_key in six.iteritems(TradePersistMap):
            if persist_key == "_order_id":
                continue
            setattr(trade, origin_key, trade_dict[persist_key])
        trade._order = order
        return trade

    def __to_dict__(self):
        trade_dict = {}
        for persist_key, origin_key in six.iteritems(TradePersistMap):
            if persist_key == "_order_id":
                trade_dict["_order_id"] = self._order.order_id
            else:
                trade_dict[persist_key] = getattr(self, origin_key)
        return trade_dict

    @property
    def trading_datetime(self):
        return self._trading_dt

    @property
    def datetime(self):
        return self._calendar_dt

    @property
    def order_id(self):
        return self.order.order_id

    @property
    def last_price(self):
        return self._price

    @property
    def last_quantity(self):
        return self._amount

    @property
    def order(self):
        return self._order

    @property
    def commission(self):
        return self._commission

    @property
    def tax(self):
        return self._tax

    @property
    def transaction_cost(self):
        return self._tax + self._commission

    @property
    def position_effect(self):
        return self.order.position_effect

    @property
    def exec_id(self):
        return self._trade_id

    def __simple_object__(self):
        return properties(self)
