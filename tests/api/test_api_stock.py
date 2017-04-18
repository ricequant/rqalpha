#!/usr/bin/env python
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

from .test_api_base import get_code_block


def test_order_shares():
    from rqalpha.api import order_shares, get_order, SIDE, LimitOrder

    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.limitprice = 8.59
        context.amount = 10000

        pass

    def handle_bar(context, bar_dict):
        order_id = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
        order = get_order(order_id)
        order_side = SIDE.BUY if context.amount > 0 else SIDE.SELL
        assert order.side == order_side, 'order.side is wrong'
        assert order.order_book_id == context.s1, 'Order_book_id is wrong'
        assert order.quantity == context.amount, 'order.quantity is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.price == context.limitprice, 'order.price is wrong'
test_order_shares_code_new = get_code_block(test_order_shares)


def test_order_lots():
    from rqalpha.api import order_lots, get_order, SIDE, LimitOrder

    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.limitprice = 8.59
        context.amount = 10000

        pass

    def handle_bar(context, bar_dict):
        order_id = order_lots(context.s1, 1, style=LimitOrder(context.limitprice))
        order = get_order(order_id)
        order_side = SIDE.BUY if context.amount > 0 else SIDE.SELL
        assert order.side == order_side, 'order.side is wrong'
        assert order.order_book_id == context.s1, 'Order_book_id is wrong'
        assert order.quantity == 100, 'order.quantity is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.price == context.limitprice, 'order.price is wrong'
test_order_lots_code_new = get_code_block(test_order_lots)


def test_order_value():
    from rqalpha.api import order_value, get_order, SIDE, LimitOrder

    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.limitprice = 8.59
        context.amount = 10000

    def handle_bar(context, bar_dict):
        order_id = order_value(context.s1, 1000, style=LimitOrder(context.limitprice))
        order = get_order(order_id)
        order_side = SIDE.BUY if order.quantity > 0 else SIDE.SELL
        assert order.side == order_side, 'order.side is wrong'
        assert order.order_book_id == context.s1, 'Order_book_id is wrong'
        assert order.quantity == 100, 'order.quantity is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.price == context.limitprice, 'order.price is wrong'
test_order_value_code_new = get_code_block(test_order_value)


def test_order_percent():
    from rqalpha.api import order_percent, get_order, SIDE, LimitOrder

    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.limitprice = 8.59
        context.amount = 10000

    def handle_bar(context, bar_dict):
        order_id = order_percent(context.s1, 0.0001, style=LimitOrder(context.limitprice))
        order = get_order(order_id)
        order_side = SIDE.BUY if order.quantity > 0 else SIDE.SELL
        assert order.side == order_side, 'order.side is wrong'
        assert order.order_book_id == context.s1, 'Order_book_id is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.price == context.limitprice, 'order.price is wrong'
test_order_percent_code_new = get_code_block(test_order_percent)


def test_order_target_value():
    from rqalpha.api import order_target_percent, get_order, SIDE, LimitOrder

    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.limitprice = 8.59
        context.amount = 10000

    def handle_bar(context, bar_dict):
        order_id = order_target_percent(context.s1, 0.02, style=LimitOrder(context.limitprice))
        print("after: ", context.portfolio.cash)
        order = get_order(order_id)
        order_side = SIDE.BUY if order.quantity > 0 else SIDE.SELL
        assert order.side == order_side, 'order.side is wrong'
        assert order.order_book_id == context.s1, 'Order_book_id is wrong'
        assert order.price == context.limitprice, 'order.price is wrong'
test_order_target_value_code_new = get_code_block(test_order_target_value)
