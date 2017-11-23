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
from rqalpha.utils.exception import patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.environment import Environment


class BaseSlippage(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_trade_price(self, order, price):
        raise NotImplementedError


class PriceRatioSlippage(BaseSlippage):
    def __init__(self, rate=0.):
        # Rate必须在0~1之间
        if 0 <= rate < 1:
            self.rate = rate
        else:
            raise patch_user_exc(ValueError(_(u"invalid slippage rate value: value range is [0, 1)")))

    def get_trade_price(self, order, price):
        side = order.side
        return price + price * self.rate * (1 if side == SIDE.BUY else -1)


class TickSizeSlippage(BaseSlippage):
    def __init__(self, rate=0.):
        if 0 <= rate:
            self.rate = rate
        else:
            raise patch_user_exc(ValueError(_(u"invalid slippage rate value: value range is greater than 0")))

    def get_trade_price(self, order, price):
        side = order.side
        tick_size = Environment.get_instance().data_proxy.instruments(order.order_book_id).tick_size()

        price = price + tick_size * self.rate * (1 if side == SIDE.BUY else -1)

        if price <= 0:
            raise patch_user_exc(ValueError(_(u"invalid slippage rate value {} which cause price <= 0").format(self.rate)))

        return price


# class FixedSlippage(BaseSlippage):
#     def __init__(self, rate=0.):
#         self.rate = rate
#
#     def get_trade_price(self, price):
#         return price + price * self.rate * (0.5 if order.side == SIDE.BUY else -0.5)
