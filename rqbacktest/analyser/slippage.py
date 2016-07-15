# -*- coding: utf-8 -*-
import abc

from six import with_metaclass, iteritems


class BaseSlippageDecider(with_metaclass(abc.ABCMeta)):
    def get_trade_price(self, data_proxy, order):
        raise NotImplementedError


class FixedPercentSlippageDecider(BaseSlippageDecider):
    def __init__(self, rate=0.246):
        self.rate = rate / 100.

    def get_trade_price(self, data_proxy, order):
        bar = data_proxy.latest_bar(order.order_book_id)

        slippage = bar.close * self.rate / 2 * (1 if order.is_buy else -1)
        trade_price = bar.close + slippage

        return trade_price
