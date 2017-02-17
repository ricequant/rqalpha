#!/usr/bin/env python
# encoding: utf-8
import inspect

def test_buy_open():
    from rqalpha.api import buy_open, subscribe, get_order, ORDER_STATUS, POSITION_EFFECT, SIDE
    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order_id = buy_open(context.f1, 1)
        order = get_order(order_id)
        assert order.order_book_id == context.f1
        assert order.quantity == 1
        assert order.status == ORDER_STATUS.ACTIVE
        assert order.unfilled_quantity == 1
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.side == SIDE.BUY
        assert order.position_effect == POSITION_EFFECT.OPEN
test_buy_open_code_new = "".join(inspect.getsourcelines(test_buy_open)[0])


def test_sell_open():
    from rqalpha.api import sell_open, subscribe, get_order, ORDER_STATUS, POSITION_EFFECT, SIDE
    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order_id = sell_open(context.f1, 1)
        order = get_order(order_id)
        assert order.order_book_id == context.f1
        assert order.quantity == 1
        assert order.status == ORDER_STATUS.ACTIVE
        assert order.unfilled_quantity == 1
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.side == SIDE.SELL
        assert order.position_effect == POSITION_EFFECT.OPEN
test_sell_open_code_new = "".join(inspect.getsourcelines(test_sell_open)[0])


def test_buy_close():
    from rqalpha.api import buy_close, subscribe, get_order, ORDER_STATUS, POSITION_EFFECT, SIDE
    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order_id = buy_close(context.f1, 1)
        order = get_order(order_id)
        assert order.order_book_id == context.f1
        assert order.quantity == 1
        assert order.status == ORDER_STATUS.ACTIVE
        assert order.unfilled_quantity == 1
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.side == SIDE.BUY
        assert order.position_effect == POSITION_EFFECT.CLOSE
test_buy_close_code_new = "".join(inspect.getsourcelines(test_buy_close)[0])


def test_sell_close():
    from rqalpha.api import sell_close, subscribe, get_order, ORDER_STATUS, POSITION_EFFECT, SIDE
    def init(context):
        context.f1 = 'P88'
        context.amount = 1
        # context.marin_rate = 10
        subscribe(context.f1)
        context.order_count = 0
        context.order = None

    def handle_bar(context, bar_dict):
        order_id = sell_close(context.f1, 1)
        order = get_order(order_id)
        assert order.order_book_id == context.f1
        assert order.quantity == 1
        assert order.status == ORDER_STATUS.ACTIVE
        assert order.unfilled_quantity == 1
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.side == SIDE.SELL
        assert order.position_effect == POSITION_EFFECT.CLOSE
test_sell_close_code_new = "".join(inspect.getsourcelines(test_sell_close)[0])
