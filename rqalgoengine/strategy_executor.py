# -*- coding: utf-8 -*-

from .utils import ExecutionContext
from .data import BarMap


class StrategyExecutor(object):
    def __init__(self, strategy, data_proxy, trading_calendar):
        self.strategy = strategy
        self.data_proxy = data_proxy
        self.trading_calendar = trading_calendar

    def execute(self):
        data_proxy = self.data_proxy

        strategy = self.strategy
        with ExecutionContext(strategy):
            strategy.init(strategy)

        for dt in self.trading_calendar:
            strategy.now = dt

            bar_dict = BarMap(dt, data_proxy)

            with ExecutionContext(strategy):
                strategy.before_trading(strategy)

            with ExecutionContext(strategy):
                strategy.handle_bar(strategy, bar_dict)
