# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import datetime


class Scheduler:
    TRADING_DATES = None

    @classmethod
    def set_trading_dates(cls, trading_dates):
        cls.TRADING_DATES = trading_dates

    def __init__(self):
        self._registry = []
        self._today = None
        self._this_week = None
        self._this_month = None

    def _always_true(self):
        return True

    def _is_weekday(self, wd):
        return self._today.weekday() == wd

    def _is_nth_trading_day_in_week(self, n):
        try:
            return self._this_week[n] == self._today
        except IndexError:
            return False

    def _is_nth_trading_day_in_month(self, n):
        try:
            return self._this_month[n] == self._today
        except IndexError:
            return False

    def run_daily(self, func):
        self._registry.append((self._always_true, func))

    def run_weekly(self, func, weekday=None, tradingday=None):
        if (weekday is not None and tradingday is not None) or (weekday is None and tradingday is None):
            raise ValueError('select one of weekday/tradingday')

        if weekday is not None:
            if weekday < 1 or weekday > 7:
                raise ValueError('invalid weekday, should be in [1, 7]')
            self._registry.append((lambda: self._is_weekday(weekday - 1), func))
        else:
            if tradingday > 5 or tradingday < -5 or tradingday == 0:
                raise ValueError('invalid trading day, should be in [-5, 0), (0, 5]')
            if tradingday > 0:
                tradingday -= 1
            self._registry.append((lambda: self._is_nth_trading_day_in_week(tradingday), func))

    def run_monthly(self, func, tradingday):
        if tradingday > 23 or tradingday < -23 or tradingday == 0:
            raise ValueError('invalid tradingday, should be in [-23, 0), (0, 23]')
        if tradingday > 0:
            tradingday -= 1
        self._registry.append((lambda: self._is_nth_trading_day_in_month(tradingday), func))

    def next_day(self, dt, context, bars):
        if len(self._registry) == 0:
            return

        self._today = dt.date()
        if not self._this_week or self._today > self._this_week[-1]:
            self._fill_week()
        if not self._this_month or self._today > self._this_month[-1]:
            self._fill_month()

        for rule, func in self._registry:
            if rule():
                func(context, bars)

    def _fill_week(self):
        weekday = self._today.isoweekday()
        weekend = self._today + datetime.timedelta(days=7-weekday)
        week_start = weekend - datetime.timedelta(days=6)

        left = self.TRADING_DATES.searchsorted(week_start)
        right = self.TRADING_DATES.searchsorted(weekend, side='right')
        self._this_week = [d.date() for d in self.TRADING_DATES[left:right]]

    def _fill_month(self):
        try:
            month_end = self._today.replace(month=self._today.month+1, day=1)
        except ValueError:
            month_end = self._today.replace(year=self._today.year+1, month=1, day=1)

        left, right = self.TRADING_DATES.searchsorted(self._today), self.TRADING_DATES.searchsorted(month_end)
        self._this_month = [d.date() for d in self.TRADING_DATES[left:right]]


scheduler = Scheduler()
