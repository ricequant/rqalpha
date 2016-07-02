# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.events import SimulatorAStockTradingEventSource, EventType
from rqalgoengine.trading_env import TradingEnv

from .fixture import *


def test_event_source(trading_calendar):
    env = TradingEnv(trading_calendar)
    source = SimulatorAStockTradingEventSource(env)

    assert len(trading_calendar) * len(EventType) == len(list(source))
