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

from rqalpha.interface import AbstractBenchmarkProvider
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.utils.logger import system_log
from rqalpha.utils.i18n import gettext as _


class BackTestPriceSeriesBenchmarkProvider(AbstractBenchmarkProvider):
    def __init__(self, order_book_id):
        self._order_book_id = order_book_id
        self._daily_return_series = None
        self._total_return_series = None
        self._index = 0

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._on_system_init)
        event_bus.prepend_listener(EVENT.AFTER_TRADING, self._on_after_trading)

    def _on_system_init(self, _):
        env = Environment.get_instance()
        bar_count = len(env.config.base.trading_calendar) + 1
        end_date = env.config.base.end_date
        close_series = env.data_proxy.history_bars(
            self._order_book_id, bar_count, "1d", "close", end_date, skip_suspended=False, adjust_type='pre'
        )
        if len(close_series) < bar_count:
            raise RuntimeError(_("Valid benchmark: unable to load enough close price."))

        self._total_return_series = (close_series - close_series[0]) / close_series[0]

        self._daily_return_series = np.zeros((bar_count, ))
        self._daily_return_series[1:] = (close_series[1:] - close_series[:-1]) / close_series[:-1]

    def _on_after_trading(self, _):
        self._index += 1

    @property
    def daily_returns(self):
        return self._daily_return_series[self._index]

    @property
    def total_returns(self):
        return self._total_return_series[self._index]


class RealTimePriceSeriesBenchmarkProvider(AbstractBenchmarkProvider):
    def __init__(self, order_book_id):
        self._order_book_id = order_book_id

        self._daily_returns = 0
        self._total_returns = 0

        event_bus = Environment.get_instance().event_bus
        event_bus.prepend_listener(EVENT.AFTER_TRADING, self._on_after_trading)

    def _refresh_returns(self, end_date):
        env = Environment.get_instance()
        bar_count = env.data_proxy.count_trading_dates(env.config.base.start_date, end_date) + 1

        close_series = env.data_proxy.history_bars(
            self._order_book_id, bar_count, "1d", "close", end_date, skip_suspended=False, adjust_type='pre'
        )

        if len(close_series) < bar_count:
            system_log.error(_("Valid benchmark: unable to load enough close price."))

        self._daily_returns = float((close_series[-1] - close_series[-2]) / close_series[-2])
        self._total_returns = float((close_series[-1] - close_series[0]) / close_series[0])

    def _on_after_trading(self, _):
        env = Environment.get_instance()
        self._refresh_returns(env.trading_dt.date())

    @property
    def daily_returns(self):
        return self._daily_returns

    @property
    def total_returns(self):
        return self._total_returns
