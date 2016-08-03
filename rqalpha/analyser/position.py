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

from collections import defaultdict

# TODO make field readonly
# TODO use nametuple to reduce memory


class Position(object):

    def __init__(self):
        self.quantity = 0.          # int	未平仓部分的总股数。
        self.bought_quantity = 0.   # int	该证券的总买入股数，例如：如果你的投资组合并没有任何平安银行的成交，那么平安银行这个股票的仓位就是0.
        self.sold_quantity = 0.     # int	该证券的总卖出股数，例如：如果你的投资组合曾经买入过平安银行股票200股并且卖出过100股，那么这个属性会返回100.
        self.bought_value = 0.      # float	该证券的总买入的价值，等于每一个该证券的买入成交的价格*买入股数的总和。
        self.sold_value = 0.        # float	该证券的总卖出价值，等于每一个该证券的卖出成交的价格*卖出股数的总和。
        # self.total_orders = 0.      # int	该仓位的总订单的次数。
        # self.total_trades = 0.      # int	该仓位的总成交的次数。
        self.sellable = 0.          # int	该仓位可卖出股数。T＋1的市场中sellable = 所有持仓-今日买入的仓位。
        self.average_cost = 0.      # float	获得该持仓的买入均价，计算方法为每次买入的数量做加权平均。
        self.market_value = 0.      # float	获得该持仓的实时市场价值。
        self.value_percent = 0.     # float	获得该持仓的实时市场价值在总投资组合价值中所占比例，取值范围[0, 1]。

    def __repr__(self):
        return "Position({%s})" % self.__dict__


def Positions():
    return defaultdict(Position)
