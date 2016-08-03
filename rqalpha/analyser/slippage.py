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


class BaseSlippageDecider(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_trade_price(self, data_proxy, order):
        raise NotImplementedError


class FixedPercentSlippageDecider(BaseSlippageDecider):
    def __init__(self, rate=0.246):
        self.rate = rate / 100.

    def get_trade_price(self, data_proxy, order):
        bar = data_proxy.latest_bar(order.order_book_id)

        slippage = bar.close * self.rate / 2 * (1 if order.is_buy else -1)
        trade_price = bar.close + slippage

        return trade_price
