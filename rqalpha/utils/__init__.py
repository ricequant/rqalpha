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
import collections
from decimal import getcontext, ROUND_FLOOR

from contextlib import contextmanager
import numpy as np

from rqalpha.utils.exception import CustomError, CustomException
from rqalpha.const import EXC_TYPE, INSTRUMENT_TYPE, DEFAULT_ACCOUNT_TYPE, UNDERLYING_SYMBOL_PATTERN, NIGHT_TRADING_NS
from rqalpha.utils.datetime_func import TimeRange
from rqalpha.utils.default_future_info import STOCK_TRADING_PERIOD, TRADING_PERIOD_DICT
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.py2 import lru_cache


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

    def __init__(self, d=None):
        self.__dict__ = d if d is not None else dict()

        for k, v in list(six.iteritems(self.__dict__)):
            if isinstance(v, dict):
                self.__dict__[k] = RqAttrDict(v)

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def update(self, other):
        RqAttrDict._update_dict_recursive(self, other)

    def items(self):
        return six.iteritems(self.__dict__)

    iteritems = items

    def keys(self):
        return self.__dict__.keys()

    @staticmethod
    def _update_dict_recursive(target, other):
        if isinstance(other, RqAttrDict):
            other = other.__dict__
        if isinstance(target, RqAttrDict):
            target = target.__dict__

        for k, v in six.iteritems(other):
            if isinstance(v, collections.Mapping):
                r = RqAttrDict._update_dict_recursive(target.get(k, {}), v)
                target[k] = r
            else:
                target[k] = other[k]
        return target

    def convert_to_dict(self):
        result_dict = {}
        for k, v in list(six.iteritems(self.__dict__)):
            if isinstance(v, RqAttrDict):
                v = v.convert_to_dict()
            result_dict[k] = v
        return result_dict


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
    from rqalpha.model.instrument import SectorCode, SectorCodeItem

    for __, v in six.iteritems(SectorCode.__dict__):
        if isinstance(v, SectorCodeItem):
            if v.cn == s or v.en == s or v.name == s:
                return v.name
    # not found
    return s


def to_industry_code(s):
    from rqalpha.model.instrument import IndustryCode, IndustryCodeItem

    for __, v in six.iteritems(IndustryCode.__dict__):
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
    from rqalpha.environment import Environment
    from rqalpha.utils.logger import system_log

    def wrapper(*args, **kwargs):
        if not Environment.get_instance().config.extra.is_hold:
            return func(*args, **kwargs)
        else:
            system_log.debug(_(u"not run {}({}, {}) because strategy is hold").format(func, args, kwargs))

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
    elif type_str == 'PublicFund':
        return INSTRUMENT_TYPE.PUBLIC_FUND
    else:
        raise NotImplementedError


INST_TYPE_IN_STOCK_ACCOUNT = [
    INSTRUMENT_TYPE.CS,
    INSTRUMENT_TYPE.ETF,
    INSTRUMENT_TYPE.LOF,
    INSTRUMENT_TYPE.INDX,
    INSTRUMENT_TYPE.FENJI_MU,
    INSTRUMENT_TYPE.FENJI_A,
    INSTRUMENT_TYPE.FENJI_B,
    INSTRUMENT_TYPE.PUBLIC_FUND
]


@lru_cache(None)
def get_account_type(order_book_id):
    from rqalpha.environment import Environment
    instrument = Environment.get_instance().get_instrument(order_book_id)
    enum_type = instrument.enum_type
    if enum_type in INST_TYPE_IN_STOCK_ACCOUNT:
        return DEFAULT_ACCOUNT_TYPE.STOCK.name
    elif enum_type == INSTRUMENT_TYPE.FUTURE:
        return DEFAULT_ACCOUNT_TYPE.FUTURE.name
    else:
        raise NotImplementedError


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


def get_trading_period(universe, accounts):
    trading_period = []
    if DEFAULT_ACCOUNT_TYPE.STOCK.name in accounts:
        trading_period += STOCK_TRADING_PERIOD

    for order_book_id in universe:
        if get_account_type(order_book_id) == DEFAULT_ACCOUNT_TYPE.STOCK.name:
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
    from rqalpha.utils.logger import user_log

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


def is_run_from_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


def generate_account_type_dict():
    account_type_dict = {}
    for key, a_type in six.iteritems(DEFAULT_ACCOUNT_TYPE.__members__):
        account_type_dict[key] = a_type.value
    return account_type_dict


def is_valid_price(price):
    return not np.isnan(price) and price > 0 and price is not None


@contextmanager
def decimal_rounding_floor():
    original_rounding_option = getcontext().rounding
    getcontext().rounding = ROUND_FLOOR
    yield
    getcontext().rounding = original_rounding_option
