# -*- coding: utf-8 -*-

from .portfolio import Portfolio
from .position import Position


class PortfolioManager(object):
    def __init__(self, **kwargs):
        self.init_cash = kwargs.get("init_cash", 100000.)

    def on_new_trade(self, trade):
        pass

    def set_dt(self, dt):
        pass

    def on_bar_close(self):
        pass

    def on_day_close(self):
        pass
