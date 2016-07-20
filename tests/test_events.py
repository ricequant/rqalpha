# -*- coding: utf-8 -*-

from rqalpha.events import SimulatorAStockTradingEventSource
from rqalpha.const import EVENT_TYPE
from rqalpha.trading_params import TradingParams

from .fixture import *


def test_event_source(trading_params):
    source = SimulatorAStockTradingEventSource(trading_params)

    assert len(trading_params.trading_calendar) * len(EVENT_TYPE) == len(list(source))
