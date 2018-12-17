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

from rqalpha.environment import Environment
from rqalpha.const import DAYS_CNT
from rqalpha.utils.repr import property_repr


class BenchmarkPortfolio(object):
    __repr__ = property_repr

    def __init__(self, benchmark_provider, units):
        self._provider = benchmark_provider
        self._units = units

    @property
    def units(self):
        return self._units

    @property
    def daily_returns(self):
        return self._provider.daily_returns

    @property
    def total_returns(self):
        return self._provider.total_returns

    @property
    def annualized_returns(self):
        # fixme: do not rely on env
        if self.unit_net_value <= 0:
            return -1

        env = Environment.get_instance()
        date_count = float(env.data_proxy.count_trading_dates(env.config.base.start_date, env.trading_dt.date()))
        return self.unit_net_value ** (DAYS_CNT.TRADING_DAYS_A_YEAR / date_count) - 1

    @property
    def unit_net_value(self):
        return 1 + self.total_returns

    @property
    def static_unit_net_value(self):
        return self.unit_net_value / (1 + self.daily_returns)

    @property
    def total_value(self):
        return self.units * self.unit_net_value

    # Only for compatible

    @property
    def cash(self):
        return 0

    market_value = total_value
    portfolio_value = total_value
    starting_cash = units
