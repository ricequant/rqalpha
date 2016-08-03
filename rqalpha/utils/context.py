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


from functools import wraps
from contextlib import contextmanager

from ..i18n import gettext as _


class ContextStack(object):

    def __init__(self):
        self.stack = []

    def push(self, obj):
        self.stack.append(obj)

    def pop(self):
        try:
            return self.stack.pop()
        except IndexError:
            raise RuntimeError("stack is empty")

    @contextmanager
    def pushed(self, obj):
        self.push(obj)
        try:
            yield self
        finally:
            self.pop()

    @property
    def top(self):
        try:
            return self.stack[-1]
        except IndexError:
            raise RuntimeError("stack is empty")


class ExecutionContext(object):
    stack = ContextStack()

    def __init__(self, strategy_executor, phase, bar_dict=None):
        """init

        :param StrategyExecutor strategy_executor:
        :param EXECUTION_PHASE phase: current execution phase
        :param BarMap bar_dict: current bar dict
        """
        self.strategy_executor = strategy_executor
        self.phase = phase
        self.bar_dict = bar_dict

    def _push(self):
        self.stack.push(self)

    def _pop(self):
        popped = self.stack.pop()
        if popped is not self:
            raise RuntimeError("Popped wrong context")
        return self

    def __enter__(self):
        self._push()
        return self

    def __exit__(self, _type, _value, _tb):
        """
        Restore the algo instance stored in __enter__.
        """
        self._pop()

    @classmethod
    def get_active(cls):
        return cls.stack.top

    @classmethod
    def get_strategy_context(cls):
        ctx = cls.get_active()
        return ctx.strategy_executor.strategy_context

    @classmethod
    def get_strategy_executor(cls):
        ctx = cls.get_active()
        return ctx.strategy_executor

    @classmethod
    def get_exchange(cls):
        return cls.get_strategy_executor().exchange

    @classmethod
    def get_current_dt(cls):
        return cls.get_strategy_executor().current_dt

    @classmethod
    def get_current_bar_dict(cls):
        ctx = cls.get_active()
        return ctx.bar_dict

    @classmethod
    def get_trading_params(cls):
        return cls.get_exchange().trading_params

    @classmethod
    def enforce_phase(cls, *phases):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if cls.get_active().phase not in phases:
                    raise RuntimeError(
                        _("You can only call %s when executing %s") % (
                            func.__name__,
                            ", ".join(map(lambda x: x.name.lower(), phases))
                        )
                    )
                return func(*args, **kwargs)
            return wrapper
        return decorator
