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

import six

from .api_base import decorate_api_exc, instruments
from .api_stock import order_shares as order_stock
from .api_future import smart_order as order_future
from ..environment import Environment
from ..const import ACCOUNT_TYPE
from ..utils.arg_checker import apply_rules, verify_that
from ..model.order import LimitOrder, MarketOrder

__all__ = [
    'order',
    'order_to'
]


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


def symbol(order_book_id, split=", "):
    if isinstance(order_book_id, six.string_types):
        return "{}[{}]".format(order_book_id, instruments(order_book_id).symbol)
    else:
        s = split.join(symbol(item) for item in order_book_id)
        return s


def now_time_str(str_format="%H:%M:%S"):
    return Environment.get_instance().trading_dt.strftime(str_format)


@export_as_api
@apply_rules(verify_that('quantity').is_number())
def order(order_book_id, quantity, price=None):
    order_style = MarketOrder() if price is None else LimitOrder(price)
    position = Environment.get_instance().portfolio.positions[order_book_id]
    if position.type == ACCOUNT_TYPE.STOCK:
        return order_stock(order_book_id, quantity, order_style)
    elif position.type == ACCOUNT_TYPE.FUTURE:
        return order_future(order_book_id, quantity, order_style)
    else:
        raise NotImplementedError


@export_as_api
@apply_rules(verify_that('quantity').is_number())
def order_to(order_book_id, quantity, price=None):
    order_style = MarketOrder() if price is None else LimitOrder(price)
    position = Environment.get_instance().portfolio.positions[order_book_id]
    if position.type == ACCOUNT_TYPE.STOCK:
        return order_stock(order_book_id, quantity - position.quantity, order_style)
    elif position.type == ACCOUNT_TYPE.FUTURE:
        return order_future(order_book_id, quantity - position.buy_quantity + position.sell_quantity, order_style)
    else:
        raise NotImplementedError
