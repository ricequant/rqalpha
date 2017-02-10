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

from ...utils.repr import property_repr, dict_repr


class PositionClone:
    __repr__ = dict_repr

    def __simple_object__(self):
        return self.__dict__


class BasePosition:

    __repr__ = property_repr

    def __init__(self, order_book_id):
        self._order_book_id = order_book_id
        self._last_price = 0
        self._market_value = 0.
        self._buy_trade_value = 0.
        self._sell_trade_value = 0
        self._buy_order_value = 0.
        self._sell_order_value = 0.

        self._buy_order_quantity = 0
        self._sell_order_quantity = 0
        self._buy_trade_quantity = 0
        self._sell_trade_quantity = 0

        self._total_orders = 0
        self._total_trades = 0

        self._is_traded = False

    @property
    def market_value(self) -> float:
        """
        【float】投资组合当前所有证券仓位的市值的加总
        """
        return self._market_value

    @property
    def order_book_id(self) -> str:
        """
        【str】合约代码
        """
        return self._order_book_id

    @property
    def total_orders(self) -> int:
        """
        【int】该仓位的总订单的次数
        """
        return self._total_orders

    @property
    def total_trades(self) -> int:
        """
        【int】该仓位的总成交的次数
        """
        return self._total_trades

    @property
    def _position_value(self) -> float:
        raise NotImplementedError

    @property
    def pnl(self) -> float:
        """
        【float】持仓累计盈亏
        """
        return self._market_value + self._sell_trade_value - self._buy_trade_value

    def _clone(self):
        p = PositionClone()
        for key in dir(self):
            if "__" in key:
                continue
            setattr(p, key, getattr(self, key))
        return p

