# -*- coding: utf-8 -*-


class Trade(object):

    def __init__(self, date, order_book_id, price, amount, order_id, commission=None):
        self.date = date
        self.order_book_id = order_book_id
        self.price = price
        self.amount = amount
        self.order_id = order_id
        self.commission = commission
