# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。
import inspect
import sys
from types import FunctionType
from functools import wraps

from rqalpha.utils import unwrapper
from rqalpha.utils.exception import (
    patch_user_exc,
    patch_system_exc,
    EXC_EXT_NAME,
    RQInvalidArgument,
)
from rqalpha.const import EXC_TYPE

__all__ = []


def decorate_api_exc(func):
    f = func
    exception_checked = False
    while True:
        if getattr(f, "_rq_exception_checked", False):
            exception_checked = True
            break

        f = getattr(f, "__wrapped__", None)
        if f is None:
            break
    if not exception_checked:
        func = api_exc_patch(func)

    return func


def api_exc_patch(func):
    if isinstance(func, FunctionType):

        @wraps(func)
        def deco(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RQInvalidArgument:
                raise
            except Exception as e:
                if isinstance(e, TypeError):
                    exc_info = sys.exc_info()
                    try:
                        ret = inspect.getcallargs(unwrapper(func), *args, **kwargs)
                    except TypeError:
                        t, v, tb = exc_info
                        raise patch_user_exc(v.with_traceback(tb))

                if getattr(e, EXC_EXT_NAME, EXC_TYPE.NOTSET) == EXC_TYPE.NOTSET:
                    patch_system_exc(e)

                raise

        return deco
    return func


def register_api(name, func):
    globals()[name] = func
    __all__.append(name)


def export_as_api(func, name=None):
    if name is None:
        name = func.__name__
    __all__.append(name)

    if isinstance(func, FunctionType):
        func = decorate_api_exc(func)
    globals()[name] = func

    return func
