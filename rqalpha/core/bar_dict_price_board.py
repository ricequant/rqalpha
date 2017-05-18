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

from ..interface import AbstractPriceBoard
from ..environment import Environment
from ..events import EVENT
from ..const import ACCOUNT_TYPE


class BarDictPriceBoard(AbstractPriceBoard):
    def __init__(self):
        self._settlement_lock = False
        self._settlement_dt = None
        self._env = Environment.get_instance()
        if ACCOUNT_TYPE.FUTURE in self._env.config.base.account_list:
            self._env.event_bus.prepend_listener(EVENT.PRE_SETTLEMENT, self._lock_settlement)
            self._env.event_bus.prepend_listener(EVENT.POST_BEFORE_TRADING, self._unlock_settlement)

    @property
    def _bar_dict(self):
        return self._env.bar_dict

    def get_last_price(self, order_book_id):
        if self._settlement_lock and self._env.get_instrument(order_book_id).type == 'Future':
            return self._env.data_proxy.get_settle_price(order_book_id, self._settlement_dt)
        else:
            return self._bar_dict[order_book_id].last

    def get_limit_up(self, order_book_id):
        return self._bar_dict[order_book_id].limit_up

    def get_limit_down(self, order_book_id):
        return self._bar_dict[order_book_id].limit_down

    def _lock_settlement(self, event):
        self._settlement_lock = True
        self._settlement_dt = self._env.trading_dt

    def _unlock_settlement(self, event):
        self._settlement_lock = False

    def get_a1(self, order_book_id):
        return np.nan

    def get_b1(self, order_book_id):
        return np.nan
