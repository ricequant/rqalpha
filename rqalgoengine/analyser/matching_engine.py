# -*- coding: utf-8 -*-


class LimitOrderMatchingEngine(object):
    pass


class MarketOrderMatchingEngine(object):
    pass


class MatchingEngine(object):
    '''
    look like exchanger
    '''
    def __init__(self, limit_order_match_engine, market_order_match_engine):
        self.limit_order_match_engine = limit_order_match_engine
        self.market_order_match_engine = market_order_match_engine

    def create_order(order, order_update_cb, trade_update_cb):
        raise NotImplementedError

    def cancel_order(order, order_update_cb):
        raise NotImplementedError

    def register_match_event_listener(order_update_cb, trade_update_cb):
        raise NotImplementedError

    def on_day_close():
        pass

    def trigger_match(dt):
        pass
