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
from .base_position import BasePosition


class StockPosition(BasePosition):
    def __init__(self, order_book_id):
        super(self, StockPosition).__init__(order_book_id)
        self._quantity = 0
        self._avg_price = 0
        self._non_closeable = 0     # 当天买入的不能卖出
        self._frozen = 0            # 冻结量
        self._transaction_cost = 0  # 交易费用

    @classmethod
    def __from_dict__(cls, state):
        # order_book_id, quantity, avg_price 必需
        position = cls(state['_order_book_id'])
        position._quantity = state['_quantity']
        position._avg_price = state['_avg_price']

        # 以下字段可选
        position._non_closeable = state['_non_closeable'] if '_non_closeable' in state else 0
        position._frozen = state['_frozen'] if '_frozen' in state else 0

        return position

    def __to_dict__(self):
        return {
            '_order_book_id': self._order_book_id,
            '_quantity': self._quantity,
            '_avg_price': self._avg_price,
            '_non_closeable': self._non_closeable,
            '_frozen': self._frozen,
        }

    def apply_trade(self, trade):
        self._transaction_cost += trade.transaction_cost
        if trade.side == SIDE.BUY:
            self._avg_price = (self._avg_price * self._quantity + trade.last_quantity * trade.last_price) / (
                self._quantity + trade.last_quantity)
            self._quantity += trade.last_quantity

            if self._order_book_id not in {'510900.XSHG', '513030.XSHG', '513100.XSHG', '513500.XSHG'}:
                # 除了上述 T+0 基金，其他都是 T+1
                self._non_closeable += trade.last_quantity
        else:
            self._quantity -= trade.last_quantity
            self._frozen -= trade.last_quantity

    def apply_settlement(self):
        pass

    def split_(self, ratio):
        self._quantity *= ratio
        # split 发生时，这两个值理论上应该都是0
        self._frozen *= ratio
        self._non_closeable *= ratio

    def on_order_pending_new_(self, order):
        if order.side == SIDE.SELL:
            self._frozen += order.quantity

    def on_order_creation_reject_(self, order):
        if order.side == SIDE.SELL:
            self._frozen -= order.quantity

    def on_order_cancel_(self, order):
        if order.side == SIDE.SELL:
            self._frozen -= order.unfilled_quantity

    def after_trading_(self):
        # T+1 在结束交易时，_non_closeable 重设为0
        self._non_closeable = 0

    @property
    def quantity(self):
        """
        【int】当前持仓股数
        """
        return self._quantity

    @property
    def bought_quantity(self):
        """
        deprecated
        """
        return self._quantity

    @property
    def sold_quantity(self):
        """
        deprecated
        """
        return 0

    @property
    def bought_value(self):
        """
        deprecated
        """
        return self._quantity * self._avg_price

    @property
    def sold_value(self):
        """
        deprecated
        """
        return 0

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
        【int】该仓位可卖出股数。T＋1的市场中sellable = 所有持仓 - 今日买入的仓位 - 已冻结
        """
        return self._quantity - self._non_closeable - self._frozen

    @property
    def market_value(self):
        return self._quantity * self._last_price

    @property
    def transaction_cost(self):
        return self._transaction_cost

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
