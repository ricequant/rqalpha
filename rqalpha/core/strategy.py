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

from rqalpha.events import EVENT, Event
from rqalpha.utils import run_when_strategy_not_hold
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import ModifyExceptionFromType
from rqalpha.execution_context import ExecutionContext
from rqalpha.const import EXECUTION_PHASE, EXC_TYPE
from rqalpha.environment import Environment


class Strategy(object):
    def __init__(self, event_bus, scope, ucontext):
        self._user_context = ucontext
        self._current_universe = set()

        self._init = scope.get('init', None)
        self._handle_bar = scope.get('handle_bar', None)
        self._handle_tick = scope.get('handle_tick', None)
        func_before_trading = scope.get('before_trading', None)
        if func_before_trading is not None and func_before_trading.__code__.co_argcount > 1:
            self._before_trading = lambda context: func_before_trading(context, None)
            user_system_log.warn(_(u"deprecated parameter[bar_dict] in before_trading function."))
        else:
            self._before_trading = func_before_trading
        self._after_trading = scope.get('after_trading', None)

        if self._before_trading is not None:
            event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        if self._handle_bar is not None:
            event_bus.add_listener(EVENT.BAR, self.handle_bar)
        if self._handle_tick is not None:
            event_bus.add_listener(EVENT.TICK, self.handle_tick)
        if self._after_trading is not None:
            event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)

        self._before_day_trading = scope.get('before_day_trading', None)
        self._before_night_trading = scope.get('before_night_trading', None)
        if self._before_day_trading is not None:
            user_system_log.warn(_(u"[deprecated] before_day_trading is no longer used. use before_trading instead."))
        if self._before_night_trading is not None:
            user_system_log.warn(_(u"[deprecated] before_night_trading is no longer used. use before_trading instead."))

    @property
    def user_context(self):
        return self._user_context

    def init(self):
        if not self._init:
            return

        with ExecutionContext(EXECUTION_PHASE.ON_INIT):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._init(self._user_context)

        Environment.get_instance().event_bus.publish_event(Event(EVENT.POST_USER_INIT))

    @run_when_strategy_not_hold
    def before_trading(self, event):
        with ExecutionContext(EXECUTION_PHASE.BEFORE_TRADING):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._before_trading(self._user_context)

    @run_when_strategy_not_hold
    def handle_bar(self, event):
        bar_dict = event.bar_dict
        with ExecutionContext(EXECUTION_PHASE.ON_BAR):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._handle_bar(self._user_context, bar_dict)

    @run_when_strategy_not_hold
    def handle_tick(self, event):
        tick = event.tick
        with ExecutionContext(EXECUTION_PHASE.ON_TICK):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._handle_tick(self._user_context, tick)

    @run_when_strategy_not_hold
    def after_trading(self, event):
        with ExecutionContext(EXECUTION_PHASE.AFTER_TRADING):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._after_trading(self._user_context)
