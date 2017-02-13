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

from ...const import DAYS_CNT
from ...utils.repr import property_repr


class BasePortfolio(object):

    __repr__ = property_repr

    def __init__(self, cash, start_date, account_type):
        self._account_type = account_type
        self._yesterday_portfolio_value = cash
        self._cash = cash
        self._starting_cash = cash
        self._start_date = start_date
        self._current_date = start_date

        self._frozen_cash = 0.
        self._total_commission = 0.
        self._total_tax = 0.

        self._dividend_receivable = 0.
        self._dividend_info = {}

    @property
    def _type(self):
        return self._account_type

    @property
    def _pid(self):
        return self._account_type.value

    @property
    def daily_returns(self):
        """
        【float】当前最新一天的每日收益
        """
        return 0 if self._yesterday_portfolio_value == 0 else self.daily_pnl / self._yesterday_portfolio_value

    @property
    def starting_cash(self):
        """
        【float】回测或实盘交易给算法策略设置的初始资金
        """
        return self._starting_cash

    @property
    def start_date(self):
        """
        【datetime.datetime】策略投资组合的回测/实时模拟交易的开始日期
        """
        return self._start_date

    @property
    def frozen_cash(self):
        """
        【float】冻结资金
        """
        return self._frozen_cash

    @property
    def cash(self):
        # 可用资金
        raise NotImplementedError

    @property
    def portfolio_value(self):
        """
        【float】总权益，包含市场价值和剩余现金
        """
        # 投资组合总值
        raise NotImplementedError

    @property
    def positions(self):
        # 持仓
        raise NotImplementedError

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，当日投资组合总权益-昨日投资组合总权益
        """
        # 当日盈亏
        raise NotImplementedError

    @property
    def market_value(self):
        """
        【float】投资组合当前所有证券仓位的市值的加总
        """
        return sum(position.market_value for position in itervalues(self.positions))

    @property
    def pnl(self):
        """
        【float】当前投资组合的累计盈亏
        """
        # 总盈亏
        return self.portfolio_value - self.starting_cash

    @property
    def total_returns(self):
        """
        【float】投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        """
        # 总收益率
        return 0 if self.starting_cash == 0 else self.pnl / self.starting_cash

    @property
    def annualized_returns(self):
        """
        【float】投资组合的年化收益率
        """
        # 年化收益率
        return (1 + self.total_returns) ** (
            DAYS_CNT.DAYS_A_YEAR / float((self._current_date - self.start_date).days + 1)) - 1

    @property
    def transaction_cost(self):
        """
        【float】总费用
        """
        # 总费用
        return self._total_commission + self._total_tax
