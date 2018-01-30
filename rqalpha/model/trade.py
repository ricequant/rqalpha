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

import time

from rqalpha.utils import id_gen
from rqalpha.utils.repr import property_repr, properties
from rqalpha.environment import Environment


class Trade(object):

    __repr__ = property_repr

    trade_id_gen = id_gen(int(time.time()))

    def __init__(self):
        self._calendar_dt = None
        self._trading_dt = None
        self._price = None
        self._amount = None
        self._order_id = None
        self._commission = None
        self._tax = None
        self._trade_id = None
        self._close_today_amount = None
        self._side = None
        self._position_effect = None
        self._order_book_id = None
        self._frozen_price = None

    @classmethod
    def __from_create__(cls, order_id, price, amount, side, position_effect, order_book_id,
                        commission=0., tax=0., trade_id=None, close_today_amount=0, frozen_price=0):
        env = Environment.get_instance()
        trade = cls()
        trade._calendar_dt = env.calendar_dt
        trade._trading_dt = env.trading_dt
        trade._price = price
        trade._amount = amount
        trade._order_id = order_id
        trade._commission = commission
        trade._tax = tax
        trade._trade_id = trade_id if trade_id is not None else next(trade.trade_id_gen)
        trade._close_today_amount = close_today_amount
        trade._side = side
        trade._position_effect = position_effect
        trade._order_book_id = order_book_id
        trade._frozen_price = frozen_price
        return trade

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def trading_datetime(self):
        return self._trading_dt

    @property
    def datetime(self):
        return self._calendar_dt

    @property
    def order_id(self):
        return self._order_id

    @property
    def last_price(self):
        return self._price

    @property
    def last_quantity(self):
        return self._amount

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
    def side(self):
        return self._side

    @property
    def position_effect(self):
        return self._position_effect

    @property
    def exec_id(self):
        return self._trade_id

    @property
    def frozen_price(self):
        return self._frozen_price

    @property
    def close_today_amount(self):
        return self._close_today_amount

    def __simple_object__(self):
        return properties(self)
