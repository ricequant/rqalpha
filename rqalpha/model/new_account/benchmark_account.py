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

from .stock_account import StockAccount
from ...environment import Environment
from ...events import EVENT


class BenchmarkAccount(StockAccount):
    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)
        event_bus.add_listener(EVENT.PRE_BAR, self._on_bar)
        event_bus.add_listener(EVENT.PRE_TICK, self._on_tick)

    def _before_trading(self, event):
        if self.market_value == 0:
            trade_quantity = 