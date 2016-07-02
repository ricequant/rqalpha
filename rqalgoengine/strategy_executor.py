# -*- coding: utf-8 -*-

from .utils import ExecutionContext
from .data import BarMap, RqDataProxy
from .events import SimulatorAStockTradingEventSource, EventType


class StrategyExecutor(object):
    def __init__(self, strategy, trading_env, **kwargs):
        self.strategy = strategy
        self.trading_env = trading_env
        self.event_source = SimulatorAStockTradingEventSource(trading_env)

        self.data_proxy = kwargs.get("data_proxy", RqDataProxy())

    def execute(self):
        data_proxy = self.data_proxy

        strategy = self.strategy

        init = strategy._init
        before_trading = strategy._before_trading
        handle_bar = strategy._handle_bar

        with ExecutionContext(strategy):
            init(strategy)

        for dt, event in self.event_source:
            strategy.now = dt

            bar_dict = BarMap(dt, data_proxy)

            if event == EventType.DAY_START:
                with ExecutionContext(strategy):
                    before_trading(strategy)
            elif event == EventType.HANDLE_BAR:
                with ExecutionContext(strategy):
                    handle_bar(strategy, bar_dict)
            elif event == EventType.DAY_END:
                # handle porfolio
                pass
