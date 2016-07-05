# -*- coding: utf-8 -*-

from collections import defaultdict

from .order import Order
from .order_style import MarketOrder, LimitOrder
from .matching_engine import MatchingEngine


class OrderManager(object):
    def __init__(self):
        self.all_orders = {}
        self.open_orders = defaultdict(list)
        self.dt = None

    def set_dt(self, dt):
        self.dt = dt

    def add_order(self, order_book_id, amount, style):
        if style is None:
            style = MarketOrder()

        order = Order(self.dt, order_book_id, amount, style)

        self.open_orders[order_book_id].append(order)
        self.all_orders[order.order_id] = order

        return order.order_id

    def cancel(self, order_id):
        raise NotImplementedError

    def get_trades(self, bar_dict):
        closed_orders = []
        trades = []

        for order_book_id, orders in self.open_orders:
            pass
