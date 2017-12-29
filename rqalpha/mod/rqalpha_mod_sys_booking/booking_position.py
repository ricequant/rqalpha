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

from rqalpha.environment import Environment
from rqalpha.const import SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE


class BookingPosition(object):

    def __init__(self, order_book_id):
        self._order_book_id = order_book_id

        self._buy_old_quantity = 0
        self._sell_old_quantity = 0
        self._buy_today_quantity = 0
        self._sell_today_quantity = 0

    def __repr__(self):
        return 'BookingPosition({})'.format(self.__dict__)

    def order_book_id(self):
        """
        [Required]

        返回当前持仓的 order_book_id
        """
        return self._order_book_id

    @property
    def quantity(self):
        """
        股票API
        """
        return self._buy_old_quantity + self._buy_today_quantity

    @property
    def buy_old_quantity(self):
        """
        [int] 买方向昨仓
        """
        return self._buy_old_quantity

    @property
    def sell_old_quantity(self):
        """
        [int] 卖方向昨仓
        """
        return self._sell_old_quantity

    @property
    def buy_today_quantity(self):
        """
        [int] 买方向今仓
        """
        return self._buy_today_quantity

    @property
    def sell_today_quantity(self):
        """
        [int] 卖方向今仓
        """
        return self._sell_today_quantity

    @property
    def buy_quantity(self):
        """
        [int] 买方向持仓
        """
        return self.buy_old_quantity + self.buy_today_quantity

    @property
    def sell_quantity(self):
        """
        [int] 卖方向持仓
        """
        return self.sell_old_quantity + self.sell_today_quantity

