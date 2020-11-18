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

from typing import Callable
from functools import wraps
from contextlib import contextmanager

from rqalpha.const import EXECUTION_PHASE
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import CustomException, patch_user_exc
from rqalpha.environment import Environment


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
        # type: () -> EXECUTION_PHASE
        try:
            return self.stack[-1]
        except IndexError:
            raise RuntimeError("stack is empty")


class ExecutionContext(object):
    stack = ContextStack()

    def __init__(self, phase):
        # type: (EXECUTION_PHASE) -> None
        self.phase = phase

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

        from rqalpha.utils import create_custom_exception
        strategy_file = Environment.get_instance().config.base.strategy_file
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, strategy_file)
        raise user_exc

    @classmethod
    def enforce_phase(cls, *phases):
        # type: (*EXECUTION_PHASE) -> Callable
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                phase = cls.stack.top.phase
                if phase not in phases:
                    raise patch_user_exc(
                        RuntimeError(_(u"You cannot call %s when executing %s") % (func.__name__, phase.value)))
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def phase(cls):
        # type: () -> EXECUTION_PHASE
        return cls.stack.top.phase
