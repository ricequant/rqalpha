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

from inspect import signature
from typing import Callable, Union, Iterable
from functools import wraps, lru_cache as origin_lru_cache

cached_functions = []


def lru_cache(*args, **kwargs):
    def decorator(func):
        func = origin_lru_cache(*args, **kwargs)(func)
        cached_functions.append(func)
        return func

    return decorator


def clear_all_cached_functions():
    for func in cached_functions:
        func.cache_clear()


def instype_singledispatch(func):
    from rqalpha.model.instrument import Instrument
    from rqalpha.const import INSTRUMENT_TYPE
    from rqalpha.utils.exception import RQInvalidArgument, RQApiNotSupportedError
    from rqalpha.utils.i18n import gettext as _

    registry = {}
    data_proxy = None

    def rq_invalid_argument(arg):
        if registry:
            return RQInvalidArgument(_(
                u"function {}: invalid {} argument, "
                u"expected an order_book_id or instrument with types {}, got {} (type: {})"
            ).format(funcname, argname, [getattr(i, "name", str(i)) for i in registry], arg, type(arg)))
        else:
            return RQApiNotSupportedError(_(
                "function {} are not supported, please check your account or mod config"
            ).format(funcname))

    @lru_cache(1024)
    def dispatch(id_or_ins):
        nonlocal data_proxy
        if isinstance(id_or_ins, Instrument):
            instype = id_or_ins.type
        else:
            if not data_proxy:
                from rqalpha.environment import Environment
                data_proxy = Environment.get_instance().data_proxy
            ins = data_proxy.instruments(id_or_ins)
            if not ins:
                raise rq_invalid_argument(id_or_ins)
            instype = ins.type
        try:
            return registry[instype]
        except KeyError:
            raise rq_invalid_argument(id_or_ins)

    def register(instypes):
        # type: (Union[INSTRUMENT_TYPE, Iterable[INSTRUMENT_TYPE]]) -> Callable
        if isinstance(instypes, str):
            instypes = [instypes]

        def register_wrapper(f):
            for instype in instypes:
                registry[instype] = f
            return f

        return register_wrapper

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not args:
            try:
                arg = kwargs[argname]
            except KeyError:
                raise TypeError('{}() missing 1 required positional argument: \'{}\''.format(
                    funcname, argname
                ))
        else:
            arg = args[0]
        try:
            impl = dispatch(arg)
        except TypeError:
            raise rq_invalid_argument(arg)
        return impl(*args, **kwargs)

    funcname = getattr(func, '__name__', 'instype_singledispatch function')
    argname = next(iter(signature(func).parameters))
    wrapper.register = register

    return wrapper
