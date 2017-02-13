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

from ..const import SIDE, ACCOUNT_TYPE
from ..execution_context import ExecutionContext


def init_tax(account_type, rate=None):
    if account_type in [ACCOUNT_TYPE.STOCK, ACCOUNT_TYPE.BENCHMARK]:
        if rate is None:
            rate = 0.001
        return StockTax(rate)
    elif account_type == ACCOUNT_TYPE.FUTURE:
        if rate is None:
            rate = 0.
        return FutureTax(rate)
    else:
        raise NotImplementedError


class BaseTax(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_tax(self, trade):
        raise NotImplementedError


class StockTax(BaseTax):
    def __init__(self, rate):
        self.rate = rate

    def get_tax(self, trade):
        cost_money = trade.last_price * trade.last_quantity
        if ExecutionContext.get_instrument(trade.order.order_book_id).type == 'CS':
            return cost_money * self.rate if trade.order.side == SIDE.SELL else 0
        else:
            return 0


class FutureTax(BaseTax):
    def __init__(self, rate):
        self.rate = rate

    def get_tax(self, trade):
        return 0
