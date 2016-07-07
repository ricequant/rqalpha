# -*- coding: utf-8 -*-
import abc

from six import with_metaclass, iteritems


class BaseCommission(with_metaclass(abc.ABCMeta)):
    def get_commission(self, data_proxy, order):
        raise NotImplementedError


class AStockCommission(with_metaclass(abc.ABCMeta)):
    def __init__(self, commission_rate=0.0008, min_commission=5, tax_rate=0.001):
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.tax_rate = tax_rate

    def get_commission(self, order, trade):
        cost_money = trade.price * trade.amount
        if trade.amount > 0:
            v = cost_money * self.commission_rate
            v = max(self.min_commission, v)
        else:
            v = cost_money * self.commission_rate
            v = max(self.min_commission, v)
            v += cost_money * self.tax_rate

        return v
