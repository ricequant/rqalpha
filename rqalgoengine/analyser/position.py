# -*- coding: utf-8 -*-


class Position(object):

    def __init__(self):
        self.quantity = 0.0
        self.bought_quantity = 0.0
        self.sold_quantity = 0.0
        self.bought_value = 0.0
        self.sold_value = 0.0
        self.total_orders = 0.0
        self.total_trades = 0.0
        self.sellable = 0.0
        self.average_cost = 0.0

    def __repr__(self):
        return "Position({%s})" % self.__dict__
