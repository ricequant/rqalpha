# -*- coding: utf-8 -*-

import sys

from .analyser import Position, Portfolio, Order
from .analyser.commission import AStockCommission
from .analyser.portfolio_manager import PortfolioManager
from .analyser.simulation_exchange import SimuExchange
from .analyser.slippage import FixedPercentSlippageDecider
from .analyser.tax import AStockTax
from .const import EVENT_TYPE, EXECUTION_PHASE
from .data import BarMap, RqDataProxy
from .events import SimulatorAStockTradingEventSource
from .instruments import Instrument
from .utils import ExecutionContext


class StrategyContext(object):
    def __init__(self):
        pass

    @property
    def now(self):
        return ExecutionContext.get_current_dt()

    @property
    def slippage(self):
        raise NotImplementedError

    @property
    def commission(self):
        raise NotImplementedError

    @property
    def benchmark(self):
        raise NotImplementedError

    @property
    def short_selling_allowed(self):
        raise NotImplementedError

    @property
    def portfolio(self):
        return ExecutionContext.get_exchange().portfolio

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items() if not callable(v))
        return "Context({%s})" % (', '.join(items), )


class StrategyExecutor(object):
    def __init__(self, trading_params, data_proxy, **kwargs):
        """init

        :param Strategy strategy: current user strategy object
        :param TradingParams trading_params: current trading params
        :param DataProxy data_proxy: current data proxy to access data
        """
        self._trading_params = trading_params
        self._data_proxy = data_proxy

        self._strategy_context = kwargs.get("strategy_context")
        if self._strategy_context is None:
            self._strategy_context = StrategyContext()

        self._user_init = kwargs.get("init", lambda _: None)
        self._user_handle_bar = kwargs.get("handle_bar", lambda _, __: None)
        self._user_before_trading = kwargs.get("before_trading", lambda _: None)

        self._simu_exchange = kwargs.get("simu_exchange")
        if self._simu_exchange is None:
            self._simu_exchange = SimuExchange(data_proxy, trading_params)

        self._event_source = SimulatorAStockTradingEventSource(trading_params)
        self._current_dt = None
        self._current_universe = set()

    def execute(self):
        """run strategy

        :returns: performance results
        :rtype: pandas.DataFrame

        """
        # use local variable for performance
        data_proxy = self.data_proxy
        strategy_context = self.strategy_context
        simu_exchange = self.exchange

        init = self._user_init
        before_trading = self._user_before_trading
        handle_bar = self._user_handle_bar

        exchange_on_dt_change = simu_exchange.on_dt_change
        exchange_on_bar_close = simu_exchange.on_bar_close
        exchange_on_day_open = simu_exchange.on_day_open
        exchange_on_day_close = simu_exchange.on_day_close

        def on_dt_change(dt):
            self._current_dt = dt
            exchange_on_dt_change(dt)

        with ExecutionContext(self, EXECUTION_PHASE.INIT):
            init(strategy_context)

        for dt, event in self._event_source:
            on_dt_change(dt)

            bar_dict = BarMap(dt, self._current_universe, data_proxy)

            if event == EVENT_TYPE.DAY_START:
                with ExecutionContext(self, EXECUTION_PHASE.BEFORE_TRADING, bar_dict):
                    exchange_on_day_open()
                    before_trading(strategy_context)

            elif event == EVENT_TYPE.HANDLE_BAR:
                with ExecutionContext(self, EXECUTION_PHASE.HANDLE_BAR, bar_dict):
                    handle_bar(strategy_context, bar_dict)
                    exchange_on_bar_close(bar_dict)

            elif event == EVENT_TYPE.DAY_END:
                exchange_on_day_close()

    @property
    def strategy_context(self):
        """get current strategy

        :returns: current strategy
        :rtype: Strategy
        """
        return self._strategy_context

    @property
    def exchange(self):
        """get current exchange

        :returns: current exchange
        :rtype: SimuExchange
        """
        return self._simu_exchange

    @property
    def data_proxy(self):
        """get current data proxy

        :returns: current data proxy
        :rtype: DataProxy
        """
        return self._data_proxy

    @property
    def current_dt(self):
        """get current simu datetime

        :returns: current datetime
        :rtype: datetime.datetime
        """
        return self._current_dt
