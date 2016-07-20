# -*- coding: utf-8 -*-
import abc

from six import with_metaclass, iteritems


class BaseCommission(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_commission(self, data_proxy, order):
        raise NotImplementedError


class AStockCommission(BaseCommission):
    def __init__(self, commission_rate=0.0008, min_commission=5):
        self.commission_rate = commission_rate
        self.min_commission = min_commission

    def get_commission(self, order, trade):
        cost_money = trade.price * abs(trade.amount)
        v = cost_money * self.commission_rate
        v = max(self.min_commission, v)

        return v
