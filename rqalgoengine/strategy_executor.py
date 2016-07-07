# -*- coding: utf-8 -*-

import sys

from .utils import ExecutionContext
from .data import BarMap, RqDataProxy
from .events import SimulatorAStockTradingEventSource, EventType


class StrategyExecutor(object):
    def __init__(self, strategy, trading_env, data_proxy, **kwargs):
        self.strategy = strategy
        self.trading_env = trading_env
        self.event_source = SimulatorAStockTradingEventSource(trading_env)

        self.data_proxy = data_proxy
        self.current_bar_dict = {}

    def execute(self):
        data_proxy = self.data_proxy

        strategy = self.strategy
        simu_exchange = strategy._simu_exchange

        init = strategy._init
        before_trading = strategy._before_trading
        handle_bar = strategy._handle_bar

        on_dt_change = strategy.on_dt_change

        on_day_close = simu_exchange.on_day_close

        # run user's init
        with ExecutionContext(strategy):
            init(strategy)

        def process_bar(bar_dict):
            # run user's strategy
            handle_bar(strategy, bar_dict)

            simu_exchange.on_bar_close(bar_dict)

        for dt, event in self.event_source:
            on_dt_change(dt)

            self.current_bar_dict = bar_dict = BarMap(dt, data_proxy)

            if event == EventType.DAY_START:
                # run user's before_trading
                with ExecutionContext(strategy):
                    before_trading(strategy)
            elif event == EventType.HANDLE_BAR:
                with ExecutionContext(strategy):
                    process_bar(bar_dict)
            elif event == EventType.DAY_END:
                on_day_close()
