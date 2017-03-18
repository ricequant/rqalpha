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

from ..environment import Environment
from ..const import DAYS_CNT


class Portfolio(object):
    def __init__(self, start_date, starting_cash, static_unit_net_value, units, accounts):
        self._start_date = start_date
        self._starting_cash = starting_cash
        self._static_unit_net_value = static_unit_net_value
        self._units = units
        self._accounts = accounts

    @property
    def start_date(self):
        """
        [datetime.datetime] 策略投资组合的开始日期
        :return:
        """
        return self._start_date

    @property
    def starting_cash(self):
        """
        [float] 初始资金
        Note: 如果有出入金的话， starting_cash 需要跟着一起变化来保证pnl的计算是正确的
        """
        return self._starting_cash

    @property
    def units(self):
        """
        [float] 份额
        """
        return self._units

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        return self.total_value / self._units

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        Note: 如果存在出入金的情况，需要同时更新starting_cash
        """
        return self.total_value - self._starting_cash

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.total_value - self._static_unit_net_value * self.units

    @property
    def daily_returns(self):
        """
        [float] 当前最新一天的日收益
        """
        return 0 if self._static_unit_net_value == 0 else self.unit_net_value / self._static_unit_net_value - 1

    @property
    def total_returns(self):
        """
        [float] 累计收益率
        """
        return self.unit_net_value - 1

    @property
    def annualized_returns(self):
        """
        [float] 累计年化收益率
        """
        return self.unit_net_value ** (
            DAYS_CNT.DAYS_A_YEAR / float((Environment.get_instance().calendar_dt - self.start_date).days + 1)) - 1

    @property
    def total_value(self):
        """
        [float]总权益
        """
        return sum(account.total_value for account in self._accounts)

    @property
    def portfolio_value(self):
        """
        [Deprecated] 总权益
        """
        return self.total_value

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        raise NotImplementedError

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return sum(account.cash for account in self._accounts)

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(account.market_value for account in self._accounts)
