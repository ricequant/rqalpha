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

from __future__ import division
import pprint
import re
import six

from contextlib import contextmanager

from .exception import CustomError, CustomException
from ..const import EXC_TYPE, INSTRUMENT_TYPE, ACCOUNT_TYPE, UNDERLYING_SYMBOL_PATTERN, NIGHT_TRADING_NS
from ..utils.datetime_func import TimeRange
from ..utils.default_future_info import STOCK_TRADING_PERIOD, TRADING_PERIOD_DICT


def safe_round(value, ndigits=3):
    if isinstance(value, float):
        return round(value, ndigits)
    return value


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RqAttrDict(object):
    '''
    fuck attrdict
    '''

    def __init__(self, d=None):
        self.__dict__ = d if d is not None else dict()

        for k, v in list(six.iteritems(self.__dict__)):
            if isinstance(v, dict):
                self.__dict__[k] = RqAttrDict(v)

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __iter__(self):
        for k, v in six.iteritems(self.__dict__):
            yield k, v


def dummy_func(*args, **kwargs):
    return None


def id_gen(start=1):
    i = start
    while True:
        yield i
        i += 1


class Nop(object):
    def __init__(self):
        pass

    def nop(*args, **kw):
        pass

    def __getattr__(self, _):
        return self.nop


def to_sector_name(s):
    from ..model.instrument import SectorCode, SectorCodeItem

    for _, v in six.iteritems(SectorCode.__dict__):
        if isinstance(v, SectorCodeItem):
            if v.cn == s or v.en == s or v.name == s:
                return v.name
    # not found
    return s


def to_industry_code(s):
    from ..model.instrument import IndustryCode, IndustryCodeItem

    for _, v in six.iteritems(IndustryCode.__dict__):
        if isinstance(v, IndustryCodeItem):
            if v.name == s:
                return v.code
    return s


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


def run_when_strategy_not_hold(func):
    from ..environment import Environment
    from ..utils.logger import system_log

    def wrapper(*args, **kwargs):
        if not Environment.get_instance().is_strategy_hold:
            return func(*args, **kwargs)
        else:
            system_log.debug("not run {}({}, {}) because strategy is hold", func, args, kwargs)

    return wrapper


def merge_dicts(*dict_args):
    result = {}
    for d in dict_args:
        result.update(d)
    return result


def instrument_type_str2enum(type_str):
    if type_str == "CS":
        return INSTRUMENT_TYPE.CS
    elif type_str == "Future":
        return INSTRUMENT_TYPE.FUTURE
    elif type_str == "Option":
        return INSTRUMENT_TYPE.OPTION
    elif type_str == "ETF":
        return INSTRUMENT_TYPE.ETF
    elif type_str == "LOF":
        return INSTRUMENT_TYPE.LOF
    elif type_str == "INDX":
        return INSTRUMENT_TYPE.INDX
    elif type_str == "FenjiMu":
        return INSTRUMENT_TYPE.FENJI_MU
    elif type_str == "FenjiA":
        return INSTRUMENT_TYPE.FENJI_A
    elif type_str == "FenjiB":
        return INSTRUMENT_TYPE.FENJI_B
    else:
        raise NotImplementedError


INST_TYPE_IN_STOCK_ACCOUNT = [
    INSTRUMENT_TYPE.CS,
    INSTRUMENT_TYPE.ETF,
    INSTRUMENT_TYPE.LOF,
    INSTRUMENT_TYPE.INDX,
    INSTRUMENT_TYPE.FENJI_MU,
    INSTRUMENT_TYPE.FENJI_A,
    INSTRUMENT_TYPE.FENJI_B
]


def get_account_type(order_book_id):
    from ..execution_context import ExecutionContext
    instrument = ExecutionContext.get_instrument(order_book_id)
    enum_type = instrument.enum_type
    if enum_type in INST_TYPE_IN_STOCK_ACCOUNT:
        return ACCOUNT_TYPE.STOCK
    elif enum_type == INSTRUMENT_TYPE.FUTURE:
        return ACCOUNT_TYPE.FUTURE
    else:
        raise NotImplementedError


def exclude_benchmark_generator(accounts):
    return {k: v for k, v in six.iteritems(accounts) if k != ACCOUNT_TYPE.BENCHMARK}


def get_upper_underlying_symbol(order_book_id):
    p = re.compile(UNDERLYING_SYMBOL_PATTERN)
    result = p.findall(order_book_id)
    return result[0] if len(result) == 1 else None


def is_night_trading(universe):
    for order_book_id in universe:
        underlying_symbol = get_upper_underlying_symbol(order_book_id)
        if underlying_symbol in NIGHT_TRADING_NS:
            return True
    return False


def merge_trading_period(trading_period):
    result = []
    for time_range in sorted(trading_period):
        if result and result[-1].end >= time_range.start:
            result[-1] = TimeRange(start=result[-1].start, end=max(result[-1].end, time_range.end))
        else:
            result.append(time_range)
    return result


def get_trading_period(universe, account_list):
    trading_period = []
    if ACCOUNT_TYPE.STOCK in account_list:
        trading_period += STOCK_TRADING_PERIOD

    for order_book_id in universe:
        if get_account_type(order_book_id) == ACCOUNT_TYPE.STOCK:
            continue
        underlying_symbol = get_upper_underlying_symbol(order_book_id)
        trading_period += TRADING_PERIOD_DICT[underlying_symbol]

    return merge_trading_period(trading_period)


def is_trading(dt, trading_period):
    t = dt.time()
    for time_range in trading_period:
        if time_range.start <= t <= time_range.end:
            return True
    return False


@contextmanager
def run_with_user_log_disabled(disabled=True):
    from .logger import user_log

    if disabled:
        user_log.disable()
    try:
        yield
    finally:
        if disabled:
            user_log.enable()


def unwrapper(func):
    f2 = func
    while True:
        f = f2
        f2 = getattr(f2, "__wrapped__", None)
        if f2 is None:
            break
    return f
