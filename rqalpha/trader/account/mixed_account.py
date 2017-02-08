# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


class MixedAccount:
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


class MixedPortfolio:
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
        return self.daily_pnl / self._yesterday_portfolio_value

    @property
    def starting_cash(self):
        return sum(portfolio.starting_cash for portfolio in self._portfolio_list)

    @property
    def start_date(self):
        for portfolio in self._portfolio_list:
            return portfolio.start_date

    @property
    def frozen_cash(self):
        return sum(portfolio.frozen_cash for portfolio in self._portfolio_list)

    @property
    def cash(self):
        return sum(portfolio.cash for portfolio in self._portfolio_list)

    @property
    def portfolio_value(self):
        return sum(portfolio.portfolio_value for portfolio in self._portfolio_list)

    @property
    def positions(self) -> "MixedPositions[]":
        return MixedPositions(self._portfolio_list)

    @property
    def daily_pnl(self):
        return sum(portfolio.daily_pnl for portfolio in self._portfolio_list)

    @property
    def market_value(self):
        return sum(portfolio.market_value for portfolio in self._portfolio_list)

    @property
    def pnl(self):
        return self.portfolio_value - self.starting_cash

    @property
    def total_returns(self):
        return self.pnl / self.starting_cash

    @property
    def annualized_returns(self):
        current_date = self._portfolio_list[0]._current_date
        return (1 + self.total_returns) ** (
            DAYS_CNT.DAYS_A_YEAR / float((current_date - self.start_date).days + 1)) - 1

    @property
    def transaction_cost(self):
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
