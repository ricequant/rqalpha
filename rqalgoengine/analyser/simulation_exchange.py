# -*- coding: utf-8 -*-

from collections import defaultdict

from six import iteritems

from .order_style import MarketOrder, LimitOrder
from .order import Order
from .trade import Trade
from ..data import BarMap, RqDataProxy


class SimuExchange(object):
    def __init__(self, data_proxy):
        self.all_orders = {}
        self.open_orders = defaultdict(list)
        self.dt = None
        self.data_proxy = data_proxy
        self.trades = defaultdict(list)

    def on_dt_change(self, dt):
        self.dt = dt

    def on_day_close(self):
        bar_dict = BarMap(self.dt, self.data_proxy)
        trades, close_orders = self.create_trades(bar_dict)

        self.trades[self.dt] = trades

        for order in close_orders:
            order_list = self.open_orders[order._order_book_id]
            try:
                order_list.remove(order)
            except ValueError:
                pass

    def create_order(self, order_book_id, amount, style):
        if style is None:
            style = MarketOrder()

        order = Order(self.dt, order_book_id, amount, style)

        self.open_orders[order_book_id].append(order)
        self.all_orders[order.order_id] = order

        return order

    def cancel(self, order_id):
        raise NotImplementedError

    def get_order(self, order_id):
        return self.all_orders[order_id]

    def create_trades(self, bar_dict):
        trades = []
        close_orders = []

        for order_book_id, order_list in iteritems(self.open_orders):
            # TODO handle limit order
            for order in order_list:
                # TODO check whether can match
                price = bar_dict[order_book_id].close
                trade = Trade(
                    date=order.dt,
                    order_book_id=order_book_id,
                    price=price,
                    amount=order.quantity,
                    order_id=order.order_id,
                    commission=None
                )

                # update order
                # TODO make more trades
                order.filled_shares = order.quantity

                close_orders.append(order)
                trades.append(trade)

        return trades, close_orders
