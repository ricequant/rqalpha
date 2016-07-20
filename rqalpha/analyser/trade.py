# -*- coding: utf-8 -*-

# TODO use nametuple to reduce memory


class Trade(object):

    def __init__(self, date, order_book_id, price, amount, order_id, commission=0., tax=0.):
        self.date = date
        self.order_book_id = order_book_id
        self.price = price
        self.amount = amount
        self.order_id = order_id
        self.commission = commission
        self.tax = tax

    def __repr__(self):
        return "Trade({0})".format(self.__dict__)
