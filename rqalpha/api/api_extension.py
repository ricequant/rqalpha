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

from rqalpha.api.api_base import decorate_api_exc, instruments, cal_style
from rqalpha.environment import Environment
from rqalpha.utils.arg_checker import apply_rules, verify_that
# noinspection PyUnresolvedReferences
from rqalpha.model.order import LimitOrder, MarketOrder, Order

__all__ = [
    'order',
    'order_to'
]


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


@export_as_api
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
def order(order_book_id, quantity, price=None, style=None):
    """
    全品种通用智能调仓函数

    如果不指定 price, 则相当于下 MarketOrder

    如果 order_book_id 是股票，等同于调用 order_shares

    如果 order_book_id 是期货，则进行智能下单:

        *   quantity 表示调仓量
        *   如果 quantity 为正数，则先平 Sell 方向仓位，再开 Buy 方向仓位
        *   如果 quantity 为负数，则先平 Buy 反向仓位，再开 Sell 方向仓位

    :param order_book_id: 下单标的物
    :type order_book_id: :class:`~Instrument` object | `str`

    :param int quantity: 调仓量

    :param float price: 下单价格

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: list[:class:`~Order`]

    :example:

    ..  code-block:: python3
        :linenos:

        # 当前仓位为0
        # RB1710 多方向调仓2手：调整后变为 BUY 2手
        order('RB1710'， 2)

        # RB1710 空方向调仓3手：先平多方向2手 在开空方向1手，调整后变为 SELL 1手
        order('RB1710', -3)

    """
    style = cal_style(price, style)
    orders = Environment.get_instance().portfolio.order(order_book_id, quantity, style)

    if isinstance(orders, Order):
        return [orders]
    return orders


@export_as_api
@apply_rules(verify_that('quantity').is_number())
def order_to(order_book_id, quantity, price=None, style=None):
    """
    全品种通用智能调仓函数

    如果不指定 price, 则相当于 MarketOrder

    如果 order_book_id 是股票，则表示仓位调整到多少股

    如果 order_book_id 是期货，则进行智能调仓:

        *   quantity 表示调整至某个仓位
        *   quantity 如果为正数，则先平 SELL 方向仓位，再 BUY 方向开仓 quantity 手
        *   quantity 如果为负数，则先平 BUY 方向仓位，再 SELL 方向开仓 -quantity 手

    :param order_book_id: 下单标的物
    :type order_book_id: :class:`~Instrument` object | `str`

    :param int quantity: 调仓量

    :param float price: 下单价格

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: list[:class:`~Order`]

    :example:

    ..  code-block:: python3
        :linenos:

        # 当前仓位为0
        # RB1710 调仓至 BUY 2手
        order_to('RB1710', 2)

        # RB1710 调仓至 SELL 1手
        order_to('RB1710'， -1)

    """
    style = cal_style(price, style)
    orders = Environment.get_instance().portfolio.order(order_book_id, quantity, style, target=True)

    if isinstance(orders, Order):
        return [orders]
    return orders
