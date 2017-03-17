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

import six

from ...environment import Environment
from ...const import DAYS_CNT


class BaseAccount(object):
    def __init__(self, start_date, starting_cash, static_unit_net_value, units,
                 total_cash, positions, backward_trade_set=set()):
        self._start_date = start_date
        self._starting_cash = starting_cash
        self._units = units
        self._static_unit_net_value = static_unit_net_value
        self._positions = positions
        self._frozen_cash = 0
        self._total_cash = total_cash
        self._backward_trade_set = backward_trade_set
        self.register_event()

    def register_event(self):
        """
        注册事件
        """
        raise NotImplementedError

    def fast_forward(self, orders=None, trades=list()):
        """
        同步账户信息至最新状态
        :param orders: 订单列表，主要用来计算frozen_cash，如果为None则不计算frozen_cash
        :param trades: 交易列表，基于Trades 将当前Positions ==> 最新Positions
        """
        raise NotImplementedError

    @property
    def type(self):
        """
        [enum] 账户类型
        """
        raise NotImplementedError

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        raise NotImplementedError

    @property
    def total_value(self):
        """
        总权益
        """
        raise NotImplementedError

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        raise NotImplementedError

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        return self._positions

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
        return self._total_cash - self._frozen_cash

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(position.market_value for position in six.itervalues(self._positions))

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in six.itervalues(self._positions))

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        Note: 如果存在出入金的情况，需要同时更新starting_cash
        """
        return self.unit_net_value * self._units - self._starting_cash

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
    def portfolio_value(self):
        """
        [Deprecated] 总权益
        """
        return self.total_value
