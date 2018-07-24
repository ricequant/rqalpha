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

import numpy as np

from rqalpha.interface import AbstractPosition
from rqalpha.environment import Environment
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log


class Positions(dict):
    def __init__(self, position_cls):
        super(Positions, self).__init__()
        self._position_cls = position_cls
        self._cached_positions = {}

    def __missing__(self, key):
        if key not in self._cached_positions:
            self._cached_positions[key] = self._position_cls(key)
        return self._cached_positions[key]

    def get_or_create(self, key):
        if key not in self:
            self[key] = self._position_cls(key)
        return self[key]


class BasePosition(AbstractPosition):
    __abandon_properties__ = ["total_orders", "total_trades"]
    NaN = float('NaN')

    def __init__(self, order_book_id):
        self._order_book_id = order_book_id
        self._last_price = self.NaN

    def get_state(self):
        raise NotImplementedError

    def set_state(self, state):
        raise NotImplementedError

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def market_value(self):
        """
        [float] 当前仓位市值
        """
        raise NotImplementedError

    @property
    def transaction_cost(self):
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError

    @property
    def last_price(self):
        last_price = (self._last_price if self._last_price == self._last_price else
            Environment.get_instance().get_last_price(self._order_book_id))
        if np.isnan(last_price):
            raise RuntimeError("Last price of position {} is not supposed to be nan".format(self.order_book_id))
        return last_price

    def update_last_price(self):
        price = Environment.get_instance().get_last_price(self._order_book_id)
        if price == price:
            # 过滤掉 nan
            self._last_price = price

    # -- Function
    def is_de_listed(self):
        raise NotImplementedError

    def apply_settlement(self):
        raise NotImplementedError

    def apply_trade(self, trade):
        raise NotImplementedError

    # ------------------------------------ Abandon Property ------------------------------------

    @property
    def total_orders(self):
        """abandon"""
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('position.total_orders'))
        return 0

    @property
    def total_trades(self):
        """abandon"""
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('position.total_trades'))
        return 0

