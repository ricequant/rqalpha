#!/usr/bin/env python
# encoding: utf-8
import inspect
import datetime


def test_order_shares():
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        pass


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
        assert order.side == order_side
        assert order.order_book_id == context.s1
        assert order.quantity == context.amount
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.price == context.limitprice
test_order_shares_code_new = "".join(inspect.getsourcelines(test_order_shares)[0])


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
        assert order.side == order_side
        assert order.order_book_id == context.s1
        assert order.quantity == 100
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.price == context.limitprice
test_order_lots_code_new = "".join(inspect.getsourcelines(test_order_lots)[0])


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
        assert order.side == order_side
        assert order.order_book_id == context.s1
        assert order.quantity == 100
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.price == context.limitprice
test_order_value_code_new = "".join(inspect.getsourcelines(test_order_value)[0])


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
        assert order.side == order_side
        assert order.order_book_id == context.s1
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
        assert order.price == context.limitprice
test_order_percent_code_new = "".join(inspect.getsourcelines(test_order_percent)[0])


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
        assert order.side == order_side
        assert order.order_book_id == context.s1
        assert order.price == context.limitprice
test_order_target_value_code_new = "".join(inspect.getsourcelines(test_order_target_value)[0])
