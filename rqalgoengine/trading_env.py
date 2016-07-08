# -*- coding: utf-8 -*-

import pytz


class TradingEnv(object):
    def __init__(self, trading_calendar, **kwargs):
        self.trading_calendar = trading_calendar
        self.timezone = kwargs.get("timezone", pytz.timezone("Asia/Shanghai"))
        self.benchmark = kwargs.get("benchmark", "000300.XSHG")
