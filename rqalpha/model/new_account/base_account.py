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

from six import itervalues

from ...environment import Environment
from ...const import DAYS_CNT


class BaseAccount(object):
    def __init__(self, total_cash, daily_orders, daily_trades, positions, units, static_unit_net_value):
        config = Environment.get_instance().config
        self._start_date = config.base.start_date
        self._units = units
        self._static_unit_net_value = static_unit_net_value
        self._daily_orders = daily_orders
        self._daily_trades = daily_trades
        self._positions = positions
        self._frozen_cash = self._cal_frozen_cash(daily_orders)
        self._cash = total_cash - self._frozen_cash
        self._type = None
        self._current_date = None

    def _cal_frozen_cash(self, daily_orders):
        raise NotImplementedError

    def _get_starting_cash(self):
        raise NotImplementedError

    @property
    def type(self):
        return self._type

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        return self._positions

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        raise NotImplementedError

    @property
    def units(self):
        """
        [float] 份额
        """
        return self._units

    @property
    def start_date(self):
        """
        [datetime.datetime] 策略投资组合的开始日期
        :return:
        """
        return self._start_date

    @property
    def frozen_cash(self):
        """
        [float] 冻结资金
        """
        return self._frozen_cash

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return self._cash

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        raise NotImplementedError

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(position.market_value for position in itervalues(self._positions))

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in itervalues(self._positions))

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        Note: 如果存在出入金的情况，需要同时更新starting_cash
        """
        return self.unit_net_value * self._units - self._get_starting_cash()

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
        DAYS_CNT.DAYS_A_YEAR / float((self._current_date - self.start_date).days + 1)) - 1



    @property
    def portfolio_value(self):
        """
        [Deprecated] 动态权益
        """
        return self.unit_net_value * self._units
