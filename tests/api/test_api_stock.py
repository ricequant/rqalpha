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

from rqalpha.api import *

from ..utils import make_test_strategy_decorator, assert_order

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "accounts": {
                "stock": 100000000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
        },
    }, test_strategies)


@as_test_strategy({
    "base": {
        "start_date": "2016-06-14",
        "end_date": "2016-06-19",
    },
})
def test_order_shares():
    # FIXME: supposed to check portfolio
    def init(context):
        context.counter = 0
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):

        context.counter += 1

        if context.counter == 1:
            order_price = bar_dict[context.s1].limit_up
            o = order_shares(context.s1, 1910, order_price)
            assert_order(o, order_book_id=context.s1, side=SIDE.BUY, quantity=1900, price=order_price)
        elif context.counter == 3:
            assert context.portfolio.positions[context.s1].quantity == 2280
            o = order_shares(context.s1, -1010, bar_dict[context.s1].limit_down)
            assert_order(o, side=SIDE.SELL, quantity=1000, status=ORDER_STATUS.FILLED)
        elif context.counter == 4:
            assert context.portfolio.positions[context.s1].quantity == 1280
            o = order_shares(context.s1, -1280, bar_dict[context.s1].limit_down)
            assert_order(o, quantity=1280, status=ORDER_STATUS.FILLED)
            assert context.portfolio.positions[context.s1].quantity == 0

    return init, handle_bar


@as_test_strategy()
def test_order_lots():
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        o = order_lots(context.s1, 1, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=100, price=order_price)
    return init, handle_bar


@as_test_strategy()
def test_order_value():
    def init(context):
        context.s1 = "000001.XSHE"
        context.amount = 100

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        o = order_value(context.s1, context.amount * order_price, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=context.amount, price=order_price)
    return init, handle_bar


@as_test_strategy()
def test_order_percent():
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        o = order_percent(context.s1, 0.0001, bar_dict[context.s1].limit_up)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    return init, handle_bar


@as_test_strategy()
def test_order_target_value():
    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.amount = 10000

    def handle_bar(context, bar_dict):
        o = order_target_percent(context.s1, 0.02, style=LimitOrder(bar_dict[context.s1].limit_up))
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    return init, handle_bar
