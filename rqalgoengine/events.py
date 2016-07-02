# -*- coding: utf-8 -*-

import datetime

import pytz
from enum import Enum


EventType = Enum("EventType", "DAY_START HANDLE_BAR DAY_END")


class SimulatorAStockTradingEventSource(object):
    def __init__(self, trading_calendar):
        self.trading_calendar = trading_calendar
        self.timezone = pytz.timezone("Asia/Shanghai")
        self.generator = self.create_generator()

    def create_generator(self):
        for date in self.trading_calendar:
            yield date.replace(hour=9, minute=0, tzinfo=self.timezone), EventType.DAY_START
            yield date.replace(hour=15, minute=0, tzinfo=self.timezone), EventType.HANDLE_BAR
            yield date.replace(hour=16, minute=0, tzinfo=self.timezone), EventType.DAY_END

    def __iter__(self):
        return self

    def __next__(self):
        for date, event in self.generator:
            return date, event

        raise StopIteration

    next = __next__  # Python 2
