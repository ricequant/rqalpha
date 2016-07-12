# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.events import SimulatorAStockTradingEventSource
from rqalgoengine.const import EVENT_TYPE
from rqalgoengine.trading_params import TradingParams

from .fixture import *


def test_event_source(trading_params):
    source = SimulatorAStockTradingEventSource(trading_params)

    assert len(trading_params.trading_calendar) * len(EVENT_TYPE) == len(list(source))
