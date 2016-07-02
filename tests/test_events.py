# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.events import SimulatorAStockTradingEventSource, EventType

from .fixture import *


def test_event_source(trading_calendar):
    source = SimulatorAStockTradingEventSource(trading_calendar)

    assert len(trading_calendar) * len(EventType) == len(list(source))
