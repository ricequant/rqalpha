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


import abc

from six import with_metaclass


class BaseTax(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_tax(self, data_proxy, order):
        raise NotImplementedError


class AStockTax(BaseTax):
    def __init__(self, tax_rate=0.001):
        self.tax_rate = tax_rate

    def get_tax(self, order, trade):
        cost_money = trade.price * abs(trade.amount)
        tax = 0
        if trade.amount < 0:
            tax = cost_money * self.tax_rate

        return tax
