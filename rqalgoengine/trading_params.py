# -*- coding: utf-8 -*-

import pytz
import pandas as pd


class TradingParams(object):
    def __init__(self, trading_calendar, **kwargs):
        assert isinstance(trading_calendar, pd.Index)
        self.trading_calendar = trading_calendar
        self.timezone = kwargs.get("timezone", pytz.utc)
        self.benchmark = kwargs.get("benchmark", "000300.XSHG")
        self.frequency = kwargs.get("frequency", "1d")
