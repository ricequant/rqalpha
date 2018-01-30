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


def test_buy_open():
    from rqalpha.api import buy_open, subscribe, ORDER_STATUS, POSITION_EFFECT, SIDE

    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order = buy_open(context.f1, 1)

        assert order.order_book_id == context.f1, 'Order_book_id is wrong'
        assert order.quantity == 1, 'order.quantity is wrong'
        assert order.status == ORDER_STATUS.FILLED, 'order.status is wrong'
        assert order.unfilled_quantity == 0, 'order.unfilled_quantity is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.side == SIDE.BUY, 'order.side is wrong'
        assert order.position_effect == POSITION_EFFECT.OPEN, 'order.position_effect is wrong'
test_buy_open_code_new = get_code_block(test_buy_open)


def test_sell_open():
    from rqalpha.api import sell_open, subscribe, ORDER_STATUS, POSITION_EFFECT, SIDE

    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order = sell_open(context.f1, 1)

        assert order.order_book_id == context.f1, 'Order_book_id is wrong'
        assert order.quantity == 1, 'order.quantity is wrong'
        assert order.status == ORDER_STATUS.FILLED, 'order.status is wrong'
        assert order.unfilled_quantity == 0, 'order.unfilled_quantity is wrong'
        assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        assert order.side == SIDE.SELL, 'order.side is wrong'
        assert order.position_effect == POSITION_EFFECT.OPEN, 'order.position_effect is wrong'
test_sell_open_code_new = get_code_block(test_sell_open)


def test_buy_close():
    from rqalpha.api import buy_close, subscribe, ORDER_STATUS, POSITION_EFFECT, SIDE

    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        orders = buy_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0

        # assert order.order_book_id == context.f1, 'Order_book_id is wrong'
        # assert order.quantity == 1, 'order.quantity is wrong'
        # assert order.status == ORDER_STATUS.REJECTED, 'order.status is wrong'
        # assert order.unfilled_quantity == 1, 'order.unfilled_quantity is wrong'
        # assert order.unfilled_quantity + order.filled_quantity == order.quantity, 'order.unfilled_quantity is wrong'
        # assert order.side == SIDE.BUY, 'order.side is wrong'
        # assert order.position_effect == POSITION_EFFECT.CLOSE, 'order.position_effect is wrong'
test_buy_close_code_new = get_code_block(test_buy_close)


def test_sell_close():
    from rqalpha.api import sell_close, subscribe, ORDER_STATUS, POSITION_EFFECT, SIDE

    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        orders = sell_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0

        # assert order.order_book_id == context.f1
        # assert order.quantity == 1
        # assert order.status == ORDER_STATUS.REJECTED
        # assert order.unfilled_quantity == 1
        # assert order.unfilled_quantity + order.filled_quantity == order.quantity
        # assert order.side == SIDE.SELL
        # assert order.position_effect == POSITION_EFFECT.CLOSE
test_sell_close_code_new = get_code_block(test_sell_close)
