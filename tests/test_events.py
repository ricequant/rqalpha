# -*- coding: utf-8 -*-
from six import print_ as print

from rqbacktest.events import SimulatorAStockTradingEventSource
from rqbacktest.const import EVENT_TYPE
from rqbacktest.trading_params import TradingParams

from .fixture import *


def test_event_source(trading_params):
    source = SimulatorAStockTradingEventSource(trading_params)

    assert len(trading_params.trading_calendar) * len(EVENT_TYPE) == len(list(source))
