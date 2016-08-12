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


class BaseCommission(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_commission(self, order, trade):
        """get commission

        :param order:
        :param trade:
        :returns: commission for current trade
        :rtype: float
        """
        raise NotImplementedError


class AStockCommission(BaseCommission):
    def __init__(self, commission_rate=0.0008, min_commission=5):
        self.commission_rate = commission_rate
        self.min_commission = min_commission

    def get_commission(self, order, trade):
        cost_money = trade.price * abs(trade.amount)
        v = cost_money * self.commission_rate
        v = max(self.min_commission, v)

        return v
