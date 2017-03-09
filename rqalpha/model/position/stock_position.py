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

from ...execution_context import ExecutionContext
from ...const import ACCOUNT_TYPE, SIDE


class StockPosition(object):
    def __init__(self, order_book_id):
        self._order_book_id = order_book_id
        self._quantity = 0
        self._avg_price = 0
        self._non_closeable = 0     # 当天买入的不能卖出
        self._frozen = 0            # 冻结量
        self._bought_value = 0
        self._bought_quantity = 0
        self._sold_value = 0
        self._sold_quantity = 0
        self._total_orders = 0
        self._total_trades = 0

    @classmethod
    def __from_dict__(cls, state):
        position = cls(state['_order_book_id'])
        position._quantity = state['_quantity']
        position._avg_price = state['_avg_price']
        position._non_closeable = state['_non_closeable']
        position._frozen = state['_frozen']

        try:
            position._bought_value = state['_bought_value']
            position._bought_quantity = state['_bought_quantity']
        except KeyError:
            # 这两个值应该一起出现，否则会导致不一致
            position._bought_quantity = position._quantity
            position._bought_value = position._quantity * position._avg_price

        try:
            position._sold_quantity = state['_sold_quantity']
            position._sold_value = state['_sold_value']
        except KeyError:
            pass

        position._total_orders = state['_total_orders'] if '_total_orders' in state else 1
        position._total_trades = state['_total_trades'] if '_total_trades' in state else 1

        return position

    def __to_dict__(self):
        return {
            '_order_book_id': self._order_book_id,
            '_quantity': self._quantity,
            '_avg_price': self._avg_price,
            '_non_closeable': self._non_closeable,
            '_frozen': self._frozen,
            '_bought_value': self._bought_value,
            '_bought_quantity': self._bought_quantity,
            '_sold_value': self._sold_value,
            '_sold_quantity': self._sold_quantity,
            '_total_orders': self._total_orders,
            '_total_trades': self._total_trades
        }

    def apply_trade_(self, trade):
        if trade.side == SIDE.BUY:
            self._bought_quantity += trade.last_quantity
            self._bought_value += trade.last_quantity * trade.last_price
            self._quantity += trade.last_quantity
            self._avg_price = self._bought_value / self._bought_quantity

            if self._order_book_id not in {'510900.XSHG', '513030.XSHG', '513100.XSHG', '513500.XSHG'}:
                # 除了上述 T+0 基金，其他都是 T+1
                self._non_closeable += trade.last_quantity
        else:
            self._sold_quantity += trade.last_quantity
            self._sold_value += trade.last_price * trade.last_quantity
            self._quantity -= trade.last_quantity
            self._frozen -= trade.last_quantity

    def freeze_(self, quantity):
        self._frozen += quantity

    def unfreeze_(self, quantity):
        self._frozen -= quantity

    @property
    def quantity(self):
        """
        【int】当前持仓股数
        """
        return self._quantity

    @property
    def bought_quantity(self):
        """
        【int】该证券的总买入股数，例如：如果你的投资组合并没有任何平安银行的成交，那么平安银行这个股票的仓位就是0
        """
        return self._bought_quantity

    @property
    def sold_quantity(self):
        """
        【int】该证券的总卖出股数，例如：如果你的投资组合曾经买入过平安银行股票200股并且卖出过100股，那么这个属性会返回100
        """
        return self._sold_quantity

    @property
    def bought_value(self):
        """
        【float】该证券的总买入的价值，等于每一个该证券的 买入成交价 * 买入股数 总和
        """
        return self._bought_value

    @property
    def sold_value(self):
        """
        【float】该证券的总卖出价值，等于每一个该证券的 卖出成交价 * 卖出股数 总和
        """
        return self._sold_value

    @property
    def average_cost(self):
        """
        【已弃用】请使用 avg_price 获取持仓买入均价
        """
        return self._avg_price

    @property
    def avg_price(self):
        """
        【float】获得该持仓的买入均价，计算方法为每次买入的数量做加权平均
        """
        return self._avg_price

    @property
    def sellable(self):
        """
        【int】该仓位可卖出股数。T＋1的市场中sellable = 所有持仓-今日买入的仓位
        """
        return self._quantity - self._non_closeable - self._frozen

    @property
    def value_percent(self):
        """
        【float】获得该持仓的实时市场价值在总投资组合价值中所占比例，取值范围[0, 1]
        """
        # FIXME
        accounts = ExecutionContext.accounts
        if ACCOUNT_TYPE.STOCK not in accounts:
            # FIXME 现在无法区分这个position是stock的还是benchmark的，但是benchmark因为没有用到这个字段，所以可以暂时返0处理。
            return 0
        portfolio = accounts[ACCOUNT_TYPE.STOCK].portfolio
        return 0 if portfolio.portfolio_value == 0 else self._position_value / portfolio.portfolio_value

    def _cal_close_today_amount(self, trade_amount, side):
        return 0
