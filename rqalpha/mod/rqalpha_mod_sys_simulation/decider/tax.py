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

from rqalpha.const import SIDE
from rqalpha.environment import Environment


class BaseTax(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_tax(self, trade):
        raise NotImplementedError


class StockTax(BaseTax):
    def __init__(self, rate=None):
        if rate is None:
            self.rate = 0.001
        else:
            self.rate = rate

    def get_tax(self, trade):
        cost_money = trade.last_price * trade.last_quantity
        if Environment.get_instance().get_instrument(trade.order_book_id).type == 'CS':
            return cost_money * self.rate if trade.side == SIDE.SELL else 0
        else:
            return 0


class FutureTax(BaseTax):
    def __init__(self, rate=0):
        self.rate = rate

    def get_tax(self, trade):
        return 0
