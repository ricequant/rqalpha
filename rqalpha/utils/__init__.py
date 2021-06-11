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

from __future__ import division
import pprint
import os
import re
import collections
from decimal import getcontext, ROUND_FLOOR
from datetime import time
from typing import Optional

from contextlib import contextmanager
import numpy as np

from rqalpha.utils.exception import CustomError, CustomException
from rqalpha.const import (
    EXC_TYPE, INSTRUMENT_TYPE, DEFAULT_ACCOUNT_TYPE, UNDERLYING_SYMBOL_PATTERN, SIDE, POSITION_EFFECT,
    POSITION_DIRECTION
)
from rqalpha.utils.datetime_func import TimeRange
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.functools import lru_cache


class RqAttrDict(object):

    def __init__(self, d=None):
        self.__dict__ = d if d is not None else dict()

        for k, v in list(self.__dict__.items()):
            if isinstance(v, dict):
                self.__dict__[k] = RqAttrDict(v)

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def __bool__(self):
        return bool(self.__dict__)

    def update(self, other):
        RqAttrDict._update_dict_recursive(self, other)

    def items(self):
        return self.__dict__.items()

    iteritems = items

    def keys(self):
        return self.__dict__.keys()

    @staticmethod
    def _update_dict_recursive(target, other):
        if isinstance(other, RqAttrDict):
            other = other.__dict__
        target_dict = target.__dict__ if isinstance(target, RqAttrDict) else target

        for k, v in other.items():
            if isinstance(v, RqAttrDict):
                v = v.__dict__
            if isinstance(v, collections.Mapping):
                r = RqAttrDict._update_dict_recursive(target_dict.get(k, {}), v)
                target_dict[k] = r
            else:
                target_dict[k] = other[k]
        return target

    def convert_to_dict(self):
        result_dict = {}
        for k, v in list(self.__dict__.items()):
            if isinstance(v, RqAttrDict):
                v = v.convert_to_dict()
            result_dict[k] = v
        return result_dict


def id_gen(start=1):
    i = start
    while True:
        yield i
        i += 1


def create_custom_exception(exc_type, exc_val, exc_tb, strategy_filename):
    try:
        msg = str(exc_val)
    except:
        msg = ""

    error = CustomError()
    error.set_msg(msg)
    error.set_exc(exc_type, exc_val, exc_tb)

    import linecache

    filename = ''
    tb = exc_tb
    while tb:
        co = tb.tb_frame.f_code
        filename = co.co_filename
        if filename != strategy_filename:
            tb = tb.tb_next
            continue
        lineno = tb.tb_lineno
        func_name = co.co_name
        code = linecache.getline(filename, lineno).strip()
        error.add_stack_info(filename, lineno, func_name, code, tb.tb_frame.f_locals)
        tb = tb.tb_next

    if filename == strategy_filename:
        error.error_type = EXC_TYPE.USER_EXC

    user_exc = CustomException(error)
    return user_exc


def merge_dicts(*dict_args):
    result = {}
    for d in dict_args:
        result.update(d)
    return result


def account_type_str2enum(type_str):
    return DEFAULT_ACCOUNT_TYPE[type_str]


INST_TYPE_IN_STOCK_ACCOUNT = [
    INSTRUMENT_TYPE.CS,
    INSTRUMENT_TYPE.ETF,
    INSTRUMENT_TYPE.LOF,
    INSTRUMENT_TYPE.INDX,
    INSTRUMENT_TYPE.PUBLIC_FUND
]


def get_upper_underlying_symbol(order_book_id):
    p = re.compile(UNDERLYING_SYMBOL_PATTERN)
    result = p.findall(order_book_id)
    return result[0] if len(result) == 1 else None


def is_night_trading(universe):
    # for compatible
    from rqalpha.environment import Environment
    return Environment.get_instance().data_proxy.is_night_trading(universe)


def merge_trading_period(trading_period):
    result = []
    for time_range in sorted(set(trading_period)):
        if result and result[-1].end >= time_range.start:
            result[-1] = TimeRange(start=result[-1].start, end=max(result[-1].end, time_range.end))
        else:
            result.append(time_range)
    return result


STOCK_TRADING_PERIOD = [
    TimeRange(start=time(9, 31), end=time(11, 30)),
    TimeRange(start=time(13, 1), end=time(15, 0)),
]


def is_trading(dt, trading_period):
    t = dt.time()
    for time_range in trading_period:
        if time_range.start <= t <= time_range.end:
            return True
    return False


def unwrapper(func):
    f2 = func
    while True:
        f = f2
        f2 = getattr(f2, "__wrapped__", None)
        if f2 is None:
            break
    return f


def is_run_from_ipython():
    try:
        __IPYTHON__  # noqa
        return True
    except NameError:
        return False


def is_valid_price(price):
    return not (price is None or np.isnan(price) or price <= 0)


def get_position_direction(side, position_effect):
    # type: (SIDE, Optional[POSITION_EFFECT]) -> Optional[POSITION_DIRECTION]
    if position_effect is None:
        return POSITION_DIRECTION.LONG
    if side == SIDE.CONVERT_STOCK:
        return POSITION_DIRECTION.LONG
    if (side == SIDE.BUY and position_effect == POSITION_EFFECT.OPEN) or (side == SIDE.SELL and position_effect in (
        POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
    )):
        return POSITION_DIRECTION.LONG
    return POSITION_DIRECTION.SHORT


@contextmanager
def decimal_rounding_floor():
    original_rounding_option = getcontext().rounding
    getcontext().rounding = ROUND_FLOOR
    yield
    getcontext().rounding = original_rounding_option


RQDATAC_DEFAULT_ADDRESS = "rqdatad-pro.ricequant.com:16011"


def init_rqdatac_env(uri):
    if uri is None:
        return

    if '@' not in uri:
        uri = "tcp://{}@{}".format(uri, RQDATAC_DEFAULT_ADDRESS)

    if not re.match(r"\w*://.+:.+@.+:\d+", uri):
        raise ValueError('invalid rqdatac uri. use user:password or tcp://user:password@ip:port')

    os.environ['RQDATAC2_CONF'] = uri


# -------------- deprecated --------------

def get_trading_period(universe, accounts):
    # for compatible
    from rqalpha.environment import Environment
    trading_period = STOCK_TRADING_PERIOD if DEFAULT_ACCOUNT_TYPE.STOCK in accounts else []
    return Environment.get_instance().data_proxy.get_trading_period(universe, trading_period)
