# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.events import SimulatorAStockTradingEventSource
from rqalgoengine.const import EVENT_TYPE
from rqalgoengine.trading_env import TradingEnv

from .fixture import *


def test_event_source(trading_env):
    source = SimulatorAStockTradingEventSource(trading_env)

    assert len(trading_env.trading_calendar) * len(EVENT_TYPE) == len(list(source))
