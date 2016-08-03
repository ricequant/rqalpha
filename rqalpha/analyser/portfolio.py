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

from .position import Positions

# TODO make field readonly
# TODO use nametuple to reduce memory


class Dividend(object):
    def __init__(self, order_book_id, quantity, dividend_series):
        self.order_book_id = order_book_id
        self.quantity = quantity
        self.dividend_series = dividend_series


class Portfolio(object):

    def __init__(self):
        self.starting_cash = 0.         # float	回测或实盘交易给算法策略设置的初始资金
        self.cash = 0.                  # float	现在投资组合中剩余的现金
        self.total_returns = 0.         # float	算法投资组合至今的累积百分比收益率。计算方法是现在的投资组合价值/投资组合的初始资金。投资组合价值包含剩余现金和其市场价值。
        self.daily_returns = 0.         # float	当前最新一天的每日收益。
        self.market_value = 0.          # float	投资组合当前的市场价值（未实现/平仓的价值）
        self.portfolio_value = 0.       # float	当前投资组合的总共价值，包含市场价值和剩余现金。
        self.pnl = 0.                   # float	当前投资组合的￥盈亏
        self.annualized_returns = 0.    # float	投资组合的年化收益率
        self.dividend_receivable = 0.   # float	投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分
        self.positions = Positions()    # Dictionary	一个包含所有仓位的字典，以id_or_symbol作为键，position对象作为值，关于position的更多的信息可以在下面的部分找到。
        self.start_date = None          # DateTime	策略投资组合的回测/实时模拟交易的开始日期

        self.total_commission = 0.      # float 总的交易费
        self.total_tax = 0.             # float 总的交易税

        self._dividend_info = {}

    def __repr__(self):
        return "Portfolio({0})".format({
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        })
