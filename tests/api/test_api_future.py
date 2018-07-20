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
                "future": 10000000000
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


@as_test_strategy()
def test_buy_open():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        o = buy_open(context.f1, 1)
        assert_order(
            o, order_book_id=context.f1, quantity=1, status=ORDER_STATUS.FILLED, side=SIDE.BUY, position_effect=POSITION_EFFECT.OPEN
        )
    return init, handle_bar


@as_test_strategy()
def test_sell_open():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        o = sell_open(context.f1, 1)
        assert_order(
            o, order_book_id=context.f1, quantity=1, status=ORDER_STATUS.FILLED, side=SIDE.SELL, position_effect=POSITION_EFFECT.OPEN
        )
    return init, handle_bar


@as_test_strategy()
def test_buy_close():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        orders = buy_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0
    return init, handle_bar


@as_test_strategy()
def test_sell_close():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        orders = sell_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0
    return init, handle_bar
