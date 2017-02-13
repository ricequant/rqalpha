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

from .base_position import BasePosition
from ...execution_context import ExecutionContext
from ...const import ACCOUNT_TYPE


StockPersistMap = {
    "_order_book_id": "_order_book_id",
    "_last_price": "_last_price",
    "_market_value": "_market_value",
    "_buy_trade_value": "_buy_trade_value",
    "_sell_trade_value": "_sell_trade_value",
    "_buy_order_value": "_buy_order_value",
    "_sell_order_value": "_sell_order_value",
    "_buy_order_quantity": "_buy_order_quantity",
    "_sell_order_quantity": "_sell_order_quantity",
    "_buy_trade_quantity": "_buy_trade_quantity",
    "_sell_trade_quantity": "_sell_trade_quantity",
    "_total_orders": "_total_orders",
    "_total_trades": "_total_trades",
    "_is_traded": "_is_traded",
    "_buy_today_holding_quantity": "_buy_today_holding_quantity",
    "_avg_price": "_avg_price",
    "_de_listed_date": "_de_listed_date",
    "_transaction_cost": "_transaction_cost",
}


class StockPosition(BasePosition):

    def __init__(self, order_book_id):
        super(StockPosition, self).__init__(order_book_id)
        self._buy_today_holding_quantity = 0        # int   T+1,所以记录下来该股票今天的买单量
        self._avg_price = 0.                        # float	获得该持仓的买入均价，计算方法为每次买入的数量做加权平均。
        instrument = ExecutionContext.get_instrument(self.order_book_id)
        self._de_listed_date = None if instrument is None else instrument.de_listed_date
        self._transaction_cost = 0.

    @classmethod
    def __from_dict__(cls, position_dict):
        position = cls(position_dict["_order_book_id"])
        for persist_key, origin_key in six.iteritems(StockPersistMap):
            setattr(position, origin_key, position_dict[persist_key])
        return position

    def __to_dict__(self):
        p_dict = {}
        for persist_key, origin_key in six.iteritems(StockPersistMap):
            p_dict[persist_key] = getattr(self, origin_key)
        return p_dict

    @property
    def _position_value(self):
        return self._market_value

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
        return self._buy_trade_quantity

    @property
    def sold_quantity(self):
        """
        【int】该证券的总卖出股数，例如：如果你的投资组合曾经买入过平安银行股票200股并且卖出过100股，那么这个属性会返回100
        """
        return self._sell_trade_quantity

    @property
    def bought_value(self):
        """
        【float】该证券的总买入的价值，等于每一个该证券的 买入成交价 * 买入股数 总和
        """
        return self._buy_trade_value

    @property
    def sold_value(self):
        """
        【float】该证券的总卖出价值，等于每一个该证券的 卖出成交价 * 卖出股数 总和
        """
        return self._sell_trade_value

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
        return self._quantity - self._buy_today_holding_quantity - self._sell_order_quantity

    @property
    def _quantity(self):
        return self._buy_trade_quantity - self._sell_trade_quantity

    @property
    def transaction_cost(self):
        """
        【float】总费用
        """
        return self._transaction_cost

    @property
    def value_percent(self):
        """
        【float】获得该持仓的实时市场价值在总投资组合价值中所占比例，取值范围[0, 1]
        """
        accounts = ExecutionContext.accounts
        if ACCOUNT_TYPE.STOCK not in accounts:
            # FIXME 现在无法区分这个position是stock的还是benchmark的，但是benchmark因为没有用到这个字段，所以可以暂时返0处理。
            return 0
        portfolio = accounts[ACCOUNT_TYPE.STOCK].portfolio
        return 0 if portfolio.portfolio_value == 0 else self._position_value / portfolio.portfolio_value

    def _cal_close_today_amount(self, trade_amount, side):
        return 0
