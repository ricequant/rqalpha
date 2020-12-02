# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import datetime
import json
from typing import List, Tuple, Callable, Optional

from dateutil.parser import parse

from rqalpha.core.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.const import EXC_TYPE, EXECUTION_PHASE
from rqalpha.core.events import EVENT
from inspect import signature
from rqalpha.utils.exception import patch_user_exc, ModifyExceptionFromType


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


def _verify_function(name, func):
    if not callable(func):
        raise patch_user_exc(ValueError('scheduler.{}: func should be callable'.format(name)))
    sig = signature(func)
    if len(sig.parameters) != 2:
        raise patch_user_exc(TypeError(
            'scheduler.{}: func should take exactly 2 arguments (context, bar_dict)'.format(name)))


class Scheduler(object):
    def __init__(self, frequency):
        self._registry = []       # type: List[Tuple[Callable[[], bool], Callable[[], bool], Callable]]
        self._today = None        # type: Optional[datetime.date]
        self._this_week = None    # type: Optional[List[datetime.date]]
        self._this_month = None   # type: Optional[List[datetime.date]]
        self._last_minute = 0     # type: Optional[int]
        self._current_minute = 0  # type: Optional[int]
        self._stage = None
        self._frequency = frequency
        self._trading_calendar = None
        self._ucontext = None

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self.next_day_)
        event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading_)
        event_bus.add_listener(EVENT.BAR, self.next_bar_)

    @property
    def trading_calendar(self):
        if self._trading_calendar is not None:
            return self._trading_calendar

        self._trading_calendar = Environment.get_instance().data_proxy.get_trading_calendar()
        return self._trading_calendar

    @property
    def ucontext(self):
        if self._ucontext is not None:
            return self._ucontext

        self._ucontext = Environment.get_instance().user_strategy.user_context
        return self._ucontext

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

        if time_rule is not None and not isinstance(time_rule, int):
            raise patch_user_exc(ValueError(
                'invalid time_rule, "before_trading" or int expected, got {}'.format(repr(time_rule))
            ))

        time_rule = time_rule if time_rule else self._minutes_since_midnight(9, 31)
        return lambda: self._should_trigger(time_rule)

    @ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
    def run_daily(self, func, time_rule=None):
        _verify_function('run_daily', func)
        self._registry.append((self._always_true, self._time_rule_for(time_rule), func))

    @ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
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

    @ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT)
    def run_monthly(self, func, tradingday=None, time_rule=None, **kwargs):
        _verify_function('run_monthly', func)
        if tradingday is None and 'monthday' in kwargs:
            tradingday = kwargs.pop('monthday')

        if kwargs:
            raise patch_user_exc(ValueError('unknown argument: {}'.format(kwargs)))

        if tradingday is None:
            raise patch_user_exc(ValueError('tradingday is required'))

        if not isinstance(tradingday, int):
            raise patch_user_exc(ValueError('tradingday: <int> excpected, {} got'.format(repr(tradingday))))

        if tradingday > 23 or tradingday < -23 or tradingday == 0:
            raise patch_user_exc(ValueError('invalid tradingday, should be in [-23, 0), (0, 23]'))
        if tradingday > 0:
            tradingday -= 1

        time_checker = self._time_rule_for(time_rule)

        self._registry.append((lambda: self._is_nth_trading_day_in_month(tradingday),
                               time_checker, func))

    def next_day_(self, event):
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

    def next_bar_(self, event):
        bars = event.bar_dict
        self._current_minute = self._minutes_since_midnight(self.ucontext.now.hour, self.ucontext.now.minute)
        for day_rule, time_rule, func in self._registry:
            if day_rule() and time_rule():
                with ExecutionContext(EXECUTION_PHASE.SCHEDULED):
                    with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                        func(self.ucontext, bars)
        self._last_minute = self._current_minute

    def before_trading_(self, event):
        self._stage = 'before_trading'
        for day_rule, time_rule, func in self._registry:
            if day_rule() and time_rule():
                with ExecutionContext(EXECUTION_PHASE.BEFORE_TRADING):
                    with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                        func(self.ucontext, None)
        self._stage = None

    def _fill_week(self):
        weekday = self._today.isoweekday()
        weekend = self._today + datetime.timedelta(days=7 - weekday)
        week_start = weekend - datetime.timedelta(days=6)

        left = self.trading_calendar.searchsorted(datetime.datetime.combine(week_start, datetime.time.min))
        right = self.trading_calendar.searchsorted(datetime.datetime.combine(weekend, datetime.time.min), side='right')
        self._this_week = [d.date() for d in self.trading_calendar[left:right]]

    def _fill_month(self):
        try:
            month_end = self._today.replace(month=self._today.month + 1, day=1)
        except ValueError:
            month_end = self._today.replace(year=self._today.year + 1, month=1, day=1)

        month_begin = self._today.replace(day=1)
        left = self.trading_calendar.searchsorted(datetime.datetime.combine(month_begin, datetime.time.min))
        right = self.trading_calendar.searchsorted(datetime.datetime.combine(month_end, datetime.time.min))
        self._this_month = [d.date() for d in self.trading_calendar[left:right]]

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
