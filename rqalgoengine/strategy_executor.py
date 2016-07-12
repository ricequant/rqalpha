# -*- coding: utf-8 -*-

import sys

from .utils import ExecutionContext
from .data import BarMap, RqDataProxy
from .events import SimulatorAStockTradingEventSource
from .const import EVENT_TYPE


class StrategyExecutor(object):
    def __init__(self, strategy, trading_params, data_proxy, **kwargs):
        self.strategy = strategy
        self.trading_params = trading_params
        self.event_source = SimulatorAStockTradingEventSource(trading_params)

        self.data_proxy = data_proxy
        self.current_bar_dict = {}

        self.universe = set()

    def execute(self):
        data_proxy = self.data_proxy

        strategy = self.strategy
        simu_exchange = strategy._simu_exchange

        init = strategy._init
        before_trading = strategy._before_trading
        handle_bar = strategy._handle_bar

        on_dt_change = strategy.on_dt_change

        on_day_close = simu_exchange.on_day_close
        on_day_open = simu_exchange.on_day_open

        # run user's init
        with ExecutionContext(strategy):
            init(strategy)

        def process_bar(bar_dict):
            # run user's strategy
            handle_bar(strategy, bar_dict)

            simu_exchange.on_bar_close(bar_dict)

        for dt, event in self.event_source:
            on_dt_change(dt)

            self.current_bar_dict = bar_dict = BarMap(dt, self.universe, data_proxy)

            if event == EVENT_TYPE.DAY_START:
                # run user's before_trading
                with ExecutionContext(strategy):
                    on_day_open()
                    before_trading(strategy)
            elif event == EVENT_TYPE.HANDLE_BAR:
                with ExecutionContext(strategy):
                    process_bar(bar_dict)
            elif event == EVENT_TYPE.DAY_END:
                on_day_close()
