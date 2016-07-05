# -*- coding: utf-8 -*-

import uuid


def gen_order_id():
    return uuid.uuid4().hex


class Order(object):

    def __init__(self, dt, order_book_id, amount, style):
        self.dt = dt
        self.order_book_id = order_book_id
        self.amount = amount
        self.style = style

        self.filled_shares = 0.0
        self.quantity = 0.0
        self.reject_reason = ""

        self._order_id = gen_order_id()

    @property
    def order_id(self):
        return self._order_id

    @property
    def instrument(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError
