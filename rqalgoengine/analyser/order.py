# -*- coding: utf-8 -*-

import uuid


def gen_order_id():
    return uuid.uuid4().hex


class Order(object):

    def __init__(self, dt, order_book_id, quantity, style):
        self.dt = dt
        self._order_book_id = order_book_id
        self._style = style
        self._order_id = gen_order_id()

        self.filled_shares = 0.0
        self.quantity = quantity
        self.reject_reason = ""

    @property
    def style(self):
        return self._style

    @property
    def order_id(self):
        return self._order_id

    @property
    def instrument(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError

    def __repr__(self):
        return "Order({0})".format(self.__dict__)
