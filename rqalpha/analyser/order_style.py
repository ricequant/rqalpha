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


class OrderStyle(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_limit_price(self, is_buy):
        raise NotImplementedError


class MarketOrder(OrderStyle):

    def get_limit_price(self, _is_buy):
        return None


class LimitOrder(OrderStyle):

    def __init__(self, limit_price):
        self.limit_price = limit_price

    def get_limit_price(self, is_buy):
        return self.limit_price
