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

from .stock_account import StockAccount
from ...environment import Environment
from ...events import EVENT
from ...model.position import Positions
from ..new_position.stock_position import StockPosition


class BenchmarkAccount(StockAccount):
    def __init__(self, start_date, starting_cash, static_unit_net_value, units, total_cash,
                 positions=Positions(StockPosition), backward_trade_set=set(),
                 dividend_receivable=None):
        super(BenchmarkAccount, self).__init__(start_date, starting_cash, static_unit_net_value, units, total_cash,
                                               positions, backward_trade_set, dividend_receivable)
        self.benchmark = Environment.get_instance().config.base.benchmark

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)
        event_bus.add_listener(EVENT.PRE_BAR, self._on_bar)
        event_bus.add_listener(EVENT.PRE_TICK, self._on_tick)

    def _on_bar(self, event):
        price = event.bar_dict[self.benchmark].close
        if np.isnan(price):
            return
        if len(self._positions) == 0:
            position = self._positions[self.benchmark]
            quantity = int(self._total_cash / price)
            position._quantity = quantity
            position._avg_price = price
            self._total_cash -= quantity * price
        else:
            self._positions[self.benchmark].last_price = price

    def _on_tick(self, event):
        tick = event.tick
        if tick.order_book_id != self.benchmark:
            return
        price = tick.last
        if len(self._positions) == 0:
            position = self._positions[self.benchmark]
            quantity = int(self._total_cash / price)
            position._quantity = quantity
            position._avg_price = price
            self._total_cash -= quantity * price
        else:
            self._positions[self.benchmark].last_price = price

    def _on_settlement(self, event):
        self._static_unit_net_value = self.unit_net_value
