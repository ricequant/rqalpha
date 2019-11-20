# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, SIDE
from rqalpha.environment import Environment

from .asset_position import AssetPositionProxy


class StockPositionProxy(AssetPositionProxy):

    stock_t1 = True

    __abandon_properties__ = AssetPositionProxy.__abandon_properties__ + [
        "margin"
    ]

    def set_state(self, state):
        assert self.order_book_id == state['order_book_id']
        if "long" in state and "short" in state:
            super(StockPositionProxy, self).set_state(state)
        else:
            today_quantity = state.get("non_closable", 0)
            old_quantity = logical_old_quantity = state.get("quantity", 0) - today_quantity
            self._long.set_state({
                "old_quantity": old_quantity,
                "logical_old_quantity": logical_old_quantity,
                "today_quantity": today_quantity,
                "avg_price": state.get("avg_price", 0),
                "trade_cost": 0,
                "transaction_cost": state.get("transaction_cost")
            })

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK.name

    def split_(self, ratio):
        self._long.apply_split(ratio)

    def dividend_(self, dividend_per_share):
        self._long.apply_dividend(dividend_per_share)

    @property
    def quantity(self):
        return self._long.quantity

    @property
    def closable_quantity(self):
        order_quantity = sum(o.unfilled_quantity for o in self.open_orders if o.side == SIDE.SELL)
        return self.quantity - order_quantity

    @property
    def sellable(self):
        """
        [int] 该仓位可卖出股数。T＋1 的市场中sellable = 所有持仓 - 今日买入的仓位 - 已冻结
        """
        if self.stock_t1:
            return self.closable_quantity - self._long.non_closable
        else:
            return self.closable_quantity

    @property
    def avg_price(self):
        """
        [float] 平均开仓价格
        """
        return self._long.avg_price

    @property
    def value_percent(self):
        """
        [float] 获得该持仓的实时市场价值在股票投资组合价值中所占比例，取值范围[0, 1]
        """
        accounts = Environment.get_instance().portfolio.accounts
        if DEFAULT_ACCOUNT_TYPE.STOCK.name not in accounts:
            return 0
        total_value = accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name].total_value
        return 0 if total_value == 0 else self.market_value / total_value

    # -- Function
    def is_de_listed(self):
        """
        判断合约是否过期
        """
        env = Environment.get_instance()
        instrument = env.get_instrument(self.order_book_id)
        current_date = env.trading_dt

        if instrument.de_listed_date is not None:
            if instrument.de_listed_date.date() > env.config.base.end_date:
                return False
            if current_date >= env.data_proxy.get_previous_trading_date(instrument.de_listed_date):
                return True
        return False

    def cal_close_today_amount(self, *_):
        return 0
