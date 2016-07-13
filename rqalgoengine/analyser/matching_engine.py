# -*- coding: utf-8 -*-
import abc

from six import with_metaclass

from collections import defaultdict
from .order_style import MarketOrder, LimitOrder


class BaseMatchingEngine(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def match(self, is_buy):
        raise NotImplementedError


class LimitOrderMatchingEngine(BaseMatchingEngine):
    pass


class MarketOrderMatchingEngine(BaseMatchingEngine):
    pass


class MatchingEngine(object):
    '''
    look like exchanger
    '''
    def __init__(self, limit_order_match_engine, market_order_match_engine):
        self.limit_order_match_engine = limit_order_match_engine
        self.market_order_match_engine = market_order_match_engine

        self.open_orders = defaultdict(list)

    def create_order(self, order, order_update_cb, trade_update_cb):
        self.open_orders[order_book_id].append(order)

        if isinstance(order.style, MarketOrder):
            self.market_order_match_engine.match()
            return _create_market_order(order, order_update_cb, trade_update_cb)
        elif isinstance(order.style, LimitOrder):
            self.limit_order_match_engine.match()
            return _create_limit_order(order, order_update_cb, trade_update_cb)
        else:
            raise NotImplementedError

    def _create_market_order(self, order, order_update_cb, trade_update_cb):
        # TODO check volume
        pass

    def _create_limit_order(self, order, order_update_cb, trade_update_cb):
        pass

    def cancel_order(self, order, order_update_cb):
        raise NotImplementedError

    def register_match_event_listener(self, order_update_cb, trade_update_cb):
        raise NotImplementedError

    def on_day_close():
        raise NotImplementedError

    def trigger_match(self, dt):
        pass
