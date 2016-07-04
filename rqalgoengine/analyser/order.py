# -*- coding: utf-8 -*-


class Order(object):

    def __init__(self):
        self.filled_shares = 0.0
        self.quantity = 0.0
        self.reject_reason = ""

    @property
    def order_id(self):
        raise NotImplementedError

    @property
    def instrument(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError
