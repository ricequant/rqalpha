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

from functools import wraps
from contextlib import contextmanager

from .utils.i18n import gettext as _
from .utils.exception import CustomException, patch_user_exc


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
    config = None
    data_proxy = None
    account = None
    accounts = None
    broker = None
    calendar_dt = None
    trading_dt = None
    plots = None

    def __init__(self, phase, bar_dict=None):
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

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Restore the algo instance stored in __enter__.
        """
        if exc_type is None:
            self._pop()
            return False

        # 处理嵌套ExecutionContext
        last_exc_val = exc_val
        while isinstance(exc_val, CustomException):
            last_exc_val = exc_val
            if exc_val.error.exc_val is not None:
                exc_val = exc_val.error.exc_val
            else:
                break
        if isinstance(last_exc_val, CustomException):
            raise last_exc_val

        from .utils import create_custom_exception
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, self.config.base.strategy_file)
        raise user_exc

    @classmethod
    def get_active(cls):
        return cls.stack.top

    @classmethod
    def get_current_bar_dict(cls):
        ctx = cls.get_active()
        return ctx.bar_dict

    @classmethod
    def get_current_calendar_dt(cls):
        return ExecutionContext.calendar_dt

    @classmethod
    def get_current_trading_dt(cls):
        return ExecutionContext.trading_dt

    @classmethod
    def get_current_run_id(cls):
        return ExecutionContext.config.base.run_id

    @classmethod
    def get_instrument(cls, order_book_id):
        return ExecutionContext.data_proxy.instruments(order_book_id)

    @classmethod
    def get_data_proxy(cls):
        return ExecutionContext.data_proxy

    @classmethod
    def enforce_phase(cls, *phases):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                phase = cls.get_active().phase
                if phase not in phases:
                    raise patch_user_exc(
                        RuntimeError(_("You cannot call %s when executing %s") % (func.__name__, phase.value)))
                return func(*args, **kwargs)
            return wrapper
        return decorator
