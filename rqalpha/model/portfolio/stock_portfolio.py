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

from .base_portfolio import BasePortfolio
from ..dividend import Dividend
from ..position import Positions, PositionsClone, StockPosition
from ...utils.repr import dict_repr


StockPersistMap = {
    "_yesterday_portfolio_value": "_yesterday_portfolio_value",
    "_cash": "_cash",
    "_starting_cash": "_starting_cash",
    "_start_date": "_start_date",
    "_current_date": "_current_date",
    "_frozen_cash": "_frozen_cash",
    "_total_commission": "_total_commission",
    "_total_tax": "_total_tax",
    "_dividend_receivable": "_dividend_receivable",
    "_dividend_info": "_dividend_info",
    "_positions": "_positions",
}


# ET：如果这里修改的话，记得提醒我修改pickle那里，多谢
class StockPortfolioClone(object):
    __repr__ = dict_repr


class StockPortfolio(BasePortfolio):

    def __init__(self, cash, start_date, account_type):
        super(StockPortfolio, self).__init__(cash, start_date, account_type)
        self._positions = Positions(StockPosition)
        self._portfolio_value = None

    def restore_from_dict_(self, portfolio_dict):
        self._cash = portfolio_dict['_cash']
        self._start_date = portfolio_dict['_start_date']
        self._positions.clear()
        self._dividend_info.clear()
        for persist_key, origin_key in six.iteritems(StockPersistMap):
            if persist_key == "_dividend_info":
                tmp = {}
                for order_book_id, dividend_dict in six.iteritems(portfolio_dict[persist_key]):
                    tmp[order_book_id] = Dividend.__from_dict__(dividend_dict)
                setattr(self, origin_key, tmp)
            elif persist_key == "_positions":
                for order_book_id, position_dict in six.iteritems(portfolio_dict[persist_key]):
                    self._positions[order_book_id] = StockPosition.__from_dict__(position_dict)
            else:
                setattr(self, origin_key, portfolio_dict[persist_key])

    def __to_dict__(self):
        p_dict = {}
        for persist_key, origin_key in six.iteritems(StockPersistMap):
            if persist_key == "_dividend_info":
                p_dict[persist_key] = {oid: dividend.__to_dict__() for oid, dividend in six.iteritems(getattr(self, origin_key))}
            elif persist_key == "_positions":
                p_dict[persist_key] = {oid: position.__to_dict__() for oid, position in six.iteritems(getattr(self, origin_key))}
            else:
                p_dict[persist_key] = getattr(self, origin_key)
        return p_dict

    @property
    def cash(self):
        """
        【float】可用资金
        """
        return self._cash

    @property
    def positions(self):
        """
        【dict】一个包含股票子组合仓位的字典，以order_book_id作为键，position对象作为值，关于position的更多的信息可以在下面的部分找到。
        """
        return self._positions

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，当日投资组合总权益-昨日投资组合总权益
        """
        return self.portfolio_value - self._yesterday_portfolio_value

    @property
    def portfolio_value(self):
        """
        【float】总权益，包含市场价值和剩余现金
        """
        if self._portfolio_value is None:
            # 总资金 + Sum(position._position_value)
            self._portfolio_value = self.cash + self.frozen_cash + sum(
                position._position_value for position in six.itervalues(self.positions))

        return self._portfolio_value

    @property
    def dividend_receivable(self):
        """
        【float】投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分
        """
        return self._dividend_receivable

    def _clone(self):
        p = StockPortfolioClone()
        for key in dir(self):
            if "__" in key:
                continue
            if key == "positions":
                ps = PositionsClone(StockPosition)
                for order_book_id in self.positions:
                    ps[order_book_id] = self.positions[order_book_id]._clone()
                setattr(p, key, ps)
            else:
                setattr(p, key, getattr(self, key))
        return p
