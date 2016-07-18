# -*- coding: utf-8 -*-
import abc

from six import with_metaclass


class OrderStyle(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_limit_price(self, is_buy):
        raise NotImplementedError


class MarketOrder(OrderStyle):

    def get_limit_price(self, _is_buy):
        return None


class LimitOrder(OrderStyle):

    def __init__(self, limit_price):
        self.limit_price = limit_price

    def get_limit_price(self, is_buy):
        return self.limit_price
