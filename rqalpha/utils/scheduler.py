# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
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
import inspect
import json

from dateutil.parser import parse

from ..execution_context import ExecutionContext
from ..utils.exception import patch_user_exc, ModifyExceptionFromType
from ..const import EXC_TYPE, EXECUTION_PHASE
from ..environment import Environment
from ..events import EVENT


def market_close(hour=0, minute=0):
    minutes_since_midnight = 15 * 60 - hour * 60 - minute
    if minutes_since_midnight < 13 * 60:
        minutes_since_midnight -= 90
    return minutes_since_midnight


def market_open(hour=0, minute=0):
    minutes_since_midnight = 9 * 60 + 31 + hour * 60 + minute
    if minutes_since_midnight > 11 * 60 + 30:
        minutes_since_midnight += 90
    return minutes_since_midnight


_scheduler = None


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
def run_daily(func, time_rule=None):
    _scheduler.run_daily(func, time_rule)


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
def run_weekly(func, weekday=None, tradingday=None, time_rule=None):
    _scheduler.run_weekly(func, weekday=weekday, tradingday=tradingday, time_rule=time_rule)


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
def run_monthly(func, tradingday=None, time_rule=None, **kwargs):
    _scheduler.run_monthly(func, tradingday=tradingday, time_rule=time_rule, **kwargs)


def _verify_function(name, func):
    if not callable(func):
        raise patch_user_exc(ValueError('scheduler.{}: func should be callable'.format(name)))
    signature = inspect.signature(func)
    if len(signature.parameters) != 2:
        raise patch_user_exc(TypeError(
            'scheduler.{}: func should take exactly 2 arguments (context, bar_dict)'.format(name)))


class Scheduler(object):
    _TRADING_DATES = None

    @classmethod
    def set_trading_dates_(cls, trading_dates):
        cls._TRADING_DATES = trading_dates

    def __init__(self, frequency):
        self._registry = []
        self._today = None
        self._this_week = None
        self._this_month = None
        self._last_minute = 0
        self._current_minute = 0
        self._stage = None
        self._ucontext = None
        self._frequency = frequency

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self.next_day_)
        event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading_)
        event_bus.add_listener(EVENT.BAR, self.next_bar_)

    def set_user_context(self, ucontext):
        self._ucontext = ucontext

    @staticmethod
    def _always_true():
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

    def _should_trigger(self, n):
        # 非股票交易时间段不触发
        if self._current_minute < 9*60+31 or self._current_minute > 15*60:
            return False

        return self._last_minute < n <= self._current_minute

    def _is_before_trading(self):
        return self._stage == 'before_trading'

    def _time_rule_for(self, time_rule):
        if time_rule == 'before_trading':
            return lambda: self._is_before_trading()

        time_rule = time_rule if time_rule else self._minutes_since_midnight(9, 31)
        return lambda: self._should_trigger(time_rule)

    def run_daily(self, func, time_rule=None):
        _verify_function('run_daily', func)
        self._registry.append((self._always_true,
                               self._time_rule_for(time_rule),
                               func))

    def run_weekly(self, func, weekday=None, tradingday=None, time_rule=None):
        _verify_function('run_weekly', func)
        if (weekday is not None and tradingday is not None) or (weekday is None and tradingday is None):
            raise patch_user_exc(ValueError('select one of weekday/tradingday'))

        if weekday is not None:
            if weekday < 1 or weekday > 7:
                raise patch_user_exc(ValueError('invalid weekday, should be in [1, 7]'))
            day_checker = lambda: self._is_weekday(weekday - 1)
        else:
            if tradingday > 5 or tradingday < -5 or tradingday == 0:
                raise patch_user_exc(ValueError('invalid trading day, should be in [-5, 0), (0, 5]'))
            if tradingday > 0:
                tradingday -= 1
            day_checker = lambda: self._is_nth_trading_day_in_week(tradingday)

        time_checker = self._time_rule_for(time_rule)

        self._registry.append((day_checker, time_checker, func))

    def run_monthly(self, func, tradingday=None, time_rule=None, **kwargs):
        _verify_function('run_monthly', func)
        if tradingday is None and 'monthday' in kwargs:
            tradingday = kwargs.pop('monthday')
        if kwargs:
            raise patch_user_exc(ValueError('unknown argument: {}'.format(kwargs)))

        if tradingday is None:
            raise patch_user_exc(ValueError('tradingday is required'))

        if tradingday > 23 or tradingday < -23 or tradingday == 0:
            raise patch_user_exc(ValueError('invalid tradingday, should be in [-23, 0), (0, 23]'))
        if tradingday > 0:
            tradingday -= 1

        time_checker = self._time_rule_for(time_rule)

        self._registry.append((lambda: self._is_nth_trading_day_in_month(tradingday),
                               time_checker, func))

    def next_day_(self):
        if len(self._registry) == 0:
            return

        self._today = Environment.get_instance().trading_dt.date()
        self._last_minute = 0
        self._current_minute = 0
        if not self._this_week or self._today > self._this_week[-1]:
            self._fill_week()
        if not self._this_month or self._today > self._this_month[-1]:
            self._fill_month()

    @staticmethod
    def _minutes_since_midnight(hour, minute):
        return hour * 60 + minute

    def next_bar_(self, bars):
        with ExecutionContext(EXECUTION_PHASE.SCHEDULED, bars):
            self._current_minute = self._minutes_since_midnight(self._ucontext.now.hour, self._ucontext.now.minute)
            for day_rule, time_rule, func in self._registry:
                if day_rule() and time_rule():
                    with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                        func(self._ucontext, bars)
            self._last_minute = self._current_minute

    def before_trading_(self):
        with ExecutionContext(EXECUTION_PHASE.BEFORE_TRADING):
            self._stage = 'before_trading'
            for day_rule, time_rule, func in self._registry:
                if day_rule() and time_rule():
                    with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                        func(self._ucontext, None)
            self._stage = None

    def _fill_week(self):
        weekday = self._today.isoweekday()
        weekend = self._today + datetime.timedelta(days=7-weekday)
        week_start = weekend - datetime.timedelta(days=6)

        left = self._TRADING_DATES.searchsorted(week_start)
        right = self._TRADING_DATES.searchsorted(weekend, side='right')
        self._this_week = [d.date() for d in self._TRADING_DATES[left:right]]

    def _fill_month(self):
        try:
            month_end = self._today.replace(month=self._today.month+1, day=1)
        except ValueError:
            month_end = self._today.replace(year=self._today.year+1, month=1, day=1)

        month_begin = self._today.replace(day=1)
        left, right = self._TRADING_DATES.searchsorted(month_begin), self._TRADING_DATES.searchsorted(month_end)
        self._this_month = [d.date() for d in self._TRADING_DATES[left:right]]

    def set_state(self, state):
        r = json.loads(state.decode('utf-8'))
        self._today = parse(r['today']).date()
        self._last_minute = r['last_minute']
        self._fill_month()
        self._fill_week()

    def get_state(self):
        if self._today is None:
            return None

        return json.dumps({
            'today': self._today.strftime('%Y-%m-%d'),
            'last_minute': self._last_minute
        }).encode('utf-8')
