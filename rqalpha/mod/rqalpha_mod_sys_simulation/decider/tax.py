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

import abc
from six import with_metaclass

from rqalpha.const import SIDE, MARKET
from rqalpha.environment import Environment


class BaseTax(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_tax(self, trade):
        raise NotImplementedError


class StockTax(BaseTax):
    def __init__(self):
        self.cn_rate = 0.001
        self.hk_rate = 0.0011

    def _get_hk_tax(self, trade):
        """
        港交所收费项目繁多，按照如下逻辑计算税费：
        1. 税费比例为 0.11%，不足 1 元按 1 元记，四舍五入保留两位小数（包括印花税、交易征费、交易系统使用费）。
        2，五元固定费用（包括卖方收取的转手纸印花税、买方收取的过户费用）。
        """
        cost_money = trade.last_price * trade.last_quantity
        tax = cost_money * self.hk_rate
        if tax < 1:
            tax = 1
        else:
            tax = round(tax, 2)
        return tax + 5

    def _get_cn_tax(self, trade):
        cost_money = trade.last_price * trade.last_quantity
        return cost_money * self.cn_rate if trade.side == SIDE.SELL else 0

    def get_tax(self, trade):
        instrument = Environment.get_instance().get_instrument(trade.order_book_id)
        if instrument.type != 'CS':
            return 0
        if instrument.market == MARKET.CN:
            return self._get_cn_tax(trade)
        elif instrument.market == MARKET.HK:
            return self._get_hk_tax(trade)
        else:
            raise NotImplementedError


class FutureTax(BaseTax):
    def __init__(self, rate=0):
        self.rate = rate

    def get_tax(self, trade):
        return 0
