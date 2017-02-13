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

from ...const import DAYS_CNT, ACCOUNT_TYPE
from ...utils import merge_dicts, exclude_benchmark_generator, get_account_type
from ...utils.repr import dict_repr


class MixedAccount(object):
    def __init__(self, accounts):
        self._accounts = exclude_benchmark_generator(accounts)
        self._portfolio = MixedPortfolio([account.portfolio for account in self._accounts.values()])

    def get_portfolio(self, trading_date):
        return MixedPortfolio([account.get_portfolio(trading_date) for account in self._accounts.values()])

    def get_order(self, order_id):
        for account in self._accounts.values():
            order = account.get_order(order_id)
            if order is not None:
                return order

    def get_open_orders(self):
        result = {}
        for account in self._accounts.values():
            result.update(account.get_open_orders())
        return result

    @property
    def portfolio(self):
        return self._portfolio


class MixedPortfolio(object):
    __repr__ = dict_repr

    def __init__(self, portfolio_list):
        self._portfolio_list = portfolio_list

    @property
    def _type(self):
        return ACCOUNT_TYPE.TOTAL

    @property
    def _pid(self):
        return ACCOUNT_TYPE.TOTAL.value

    @property
    def _yesterday_portfolio_value(self):
        return sum(portfolio._yesterday_portfolio_value for portfolio in self._portfolio_list)

    @property
    def daily_returns(self):
        """
        【float】投资组合每日收益率
        """
        return self.daily_pnl / self._yesterday_portfolio_value

    @property
    def starting_cash(self):
        """
        【float】初始资金，为子组合初始资金的加总
        """
        return sum(portfolio.starting_cash for portfolio in self._portfolio_list)

    @property
    def start_date(self):
        """
        【datetime.datetime】策略投资组合的回测/实时模拟交易的开始日期
        """
        for portfolio in self._portfolio_list:
            return portfolio.start_date

    @property
    def frozen_cash(self):
        """
        【float】冻结资金
        """
        return sum(portfolio.frozen_cash for portfolio in self._portfolio_list)

    @property
    def cash(self):
        """
        【float】可用资金，为子组合可用资金的加总
        """
        return sum(portfolio.cash for portfolio in self._portfolio_list)

    @property
    def portfolio_value(self):
        """
        【float】总权益，为子组合总权益加总
        """
        return sum(portfolio.portfolio_value for portfolio in self._portfolio_list)

    @property
    def positions(self):
        """
        【dict】一个包含所有仓位的字典，以order_book_id作为键，position对象作为值，关于position的更多的信息可以在下面的部分找到。
        """
        return MixedPositions(self._portfolio_list)

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，子组合当日盈亏的加总
        """
        return sum(portfolio.daily_pnl for portfolio in self._portfolio_list)

    @property
    def market_value(self):
        """
        【float】投资组合当前的市场价值，为子组合市场价值的加总
        """
        return sum(portfolio.market_value for portfolio in self._portfolio_list)

    @property
    def pnl(self):
        """
        【float】当前投资组合的累计盈亏
        """
        return self.portfolio_value - self.starting_cash

    @property
    def total_returns(self):
        """
        【float】投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        """
        return self.pnl / self.starting_cash

    @property
    def annualized_returns(self):
        """
        【float】投资组合的年化收益率
        """
        current_date = self._portfolio_list[0]._current_date
        return (1 + self.total_returns) ** (
            DAYS_CNT.DAYS_A_YEAR / float((current_date - self.start_date).days + 1)) - 1

    @property
    def transaction_cost(self):
        """
        【float】总费用
        """
        return sum(portfolio.transaction_cost for portfolio in self._portfolio_list)


class MixedPositions(dict):
    def __init__(self, portfolio_list):
        super(MixedPositions, self).__init__()
        self.portfolio_list = portfolio_list

    def __missing__(self, order_book_id):
        account_type = get_account_type(order_book_id)
        for portfolio in self.portfolio_list:
            if portfolio._type == account_type:
                return portfolio.positions[order_book_id]
        return None

    def __repr__(self):
        keys = []
        for portfolio in self.portfolio_list:
            keys += portfolio.positions.keys()
        return str(sorted(keys))

    def __len__(self):
        return sum(len(portfolio.positions) for portfolio in self.portfolio_list)

    def __iter__(self):
        keys = []
        for portfolio in self.portfolio_list:
            keys += portfolio.positions.keys()
        for key in sorted(keys):
            yield key

    def items(self):
        items = merge_dicts(*[portfolio.positions.items() for portfolio in self.portfolio_list])
        for k in sorted(items.keys()):
            yield k, items[k]

    def keys(self):
        keys = []
        for portfolio in self.portfolio_list:
            keys += list(portfolio.positions.keys())
        return iter(sorted(keys))
