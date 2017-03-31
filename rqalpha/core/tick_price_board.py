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
from ..interface import AbstractPriceBoard
from ..environment import Environment
from ..events import EVENT
from ..const import ACCOUNT_TYPE
from ..const import ACCOUNT_TYPE


class TickPriceBoard(AbstractPriceBoard):
    def __init__(self):
        self._env = Environment.get_instance()
        self._env.event_bus.add_listener(EVENT.TICK, self._on_tick)
        self._tick_board = {}

    def _on_tick(self, tick):
        self._tick_board[tick.order_book_id] = tick

    def get_last_price(self, order_book_id):
        if self._settlement_lock:
            return self._env.data_proxy.get_settle_price(order_book_id, self._env.trading_dt)
        else:
            return self._tick_board[order_book_id].last

    def get_limit_up(self, order_book_id):
        return self._tick_board[order_book_id].limit_up

    def get_limit_down(self, order_book_id):
        return self._tick_board[order_book_id].limit_down
