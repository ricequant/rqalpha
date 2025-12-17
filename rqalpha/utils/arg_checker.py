# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import sys
import inspect
import datetime
import six
import pandas as pd
from typing import Iterable, Optional, List, Callable, Dict, Any
from functools import wraps
from contextlib import contextmanager

from dateutil.parser import parse as parse_date

from rqalpha.utils.exception import RQInvalidArgument, RQTypeError
from rqalpha.model.instrument import Instrument
from rqalpha.environment import Environment
from rqalpha.const import INSTRUMENT_TYPE, EXC_TYPE
from rqalpha.utils import unwrapper
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import patch_system_exc, EXC_EXT_NAME, InstrumentNotFound
from rqalpha.utils.logger import user_system_log


main_contract_warning_flag = True
index_contract_warning_flag = True


class ArgumentCheckerBase(object):
    """验证/转换规则的基类"""
    def __init__(self, arg_name):
        self._arg_name = arg_name
        self._rules = []

    @property
    def arg_name(self):
        return self._arg_name

    def raise_invalid_instrument_error(self, func_name, value):
        return self.raise_instrument_error(func_name, value, _("valid order_book_id/instrument"))

    def raise_instrument_not_listed_error(self, func_name, value):
        return self.raise_instrument_error(func_name, value, _("listed order_book_id/instrument"))

    def raise_instrument_error(self, func_name, value, instrument_info):
        raise RQInvalidArgument(_(
            u"function {}: invalid {} argument, expected a {}, got {} (type: {})"
        ).format(func_name, self._arg_name, instrument_info, value, type(value)))



def assure_listed_instrument(id_or_ins) -> Instrument:
    def _raise():
        raise RQInvalidArgument(_(
            u"invalid order_book_id/instrument, expected a listed order_book_id/instrument, got {} (type: {})"
        ).format(id_or_ins, type(id_or_ins)))

    if isinstance(id_or_ins, Instrument):
        if not id_or_ins.listed:
            return _raise()
        return id_or_ins
    elif isinstance(id_or_ins, six.string_types):
        env = Environment.get_instance()
        try:
            ins = env.data_proxy.instrument_not_none(id_or_ins, env.trading_dt)
        except InstrumentNotFound as e:
            return _raise()
        return ins
    else:
        return _raise()


class ArgumentChecker(ArgumentCheckerBase):
    """仅验证参数，不修改参数值"""
    def __init__(self, arg_name, pre_check):
        super().__init__(arg_name)
        self._pre_check = pre_check

    @property
    def pre_check(self):
        return self._pre_check

    def is_instance_of(self, types):
        def check_is_instance_of(func_name, value):
            if not isinstance(value, types):
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, expect a value of type {}, got {} (type: {})").format(
                        func_name, self._arg_name, types, value, type(value)
                    ))

        self._rules.append(check_is_instance_of)
        return self

    def _is_valid_instrument(self, func_name, value):
        instrument = None
        if isinstance(value, six.string_types):
            instrument = Environment.get_instance().get_instrument(value)
        elif isinstance(value, Instrument):
            instrument = value

        if instrument is None:
            self.raise_invalid_instrument_error(func_name, value)
        return instrument

    def is_listed_instrument(self):
        self._rules.append(lambda func_name, value: assure_listed_instrument(value))
        return self

    def is_valid_order_book_id(self, expected_type: Optional[INSTRUMENT_TYPE] = None):
        def check(func_name, value):
            env = Environment.get_instance()
            try:
                order_book_id = env.data_proxy.assure_order_book_id(value, expected_type)
            except InstrumentNotFound as e:
                raise RQInvalidArgument(_(f"func: {func_name}: invalid order_book_id: {value}").format(func_name, value))
            return order_book_id
        self._rules.append(check)
        return self

    def _is_number(self, func_name, value):
        try:
            v = float(value)
        except (ValueError, TypeError):
            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, expect a number, got {} (type: {})").format(
                    func_name, self._arg_name, value, type(value))
            )

    def is_number(self):
        self._rules.append(self._is_number)
        return self

    def deprecated(self, hint="deprecated"):
        def inner(func_name, value):
            if value is not None:
                content = "{} param {} is deprecated. {}".format(func_name, self._arg_name, hint)
                user_system_log.warning(content)
        self._rules.append(inner)
        return self

    def is_in(self, valid_values, ignore_none=True):
        def check_is_in(func_name, value):
            if ignore_none and value is None:
                return

            if value not in valid_values:
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, valid: {}, got {} (type: {})").format(
                        func_name, self._arg_name, repr(valid_values), value, type(value))
                )

        self._rules.append(check_is_in)
        return self

    def are_valid_fields(self, valid_fields, ignore_none=True):
        valid_fields = set(valid_fields)

        def check_are_valid_fields(func_name, fields):
            if isinstance(fields, six.string_types):
                if fields not in valid_fields:
                    raise RQInvalidArgument(
                        _(u"function {}: invalid {} argument, valid fields are {}, got {} (type: {})").format(
                            func_name, self._arg_name, repr(valid_fields), fields, type(fields)
                        ))
                return

            if fields is None and ignore_none:
                return

            if isinstance(fields, list):
                invalid_fields = [field for field in fields if field not in valid_fields]
                if invalid_fields:
                    raise RQInvalidArgument(
                        _(u"function {}: invalid field {}, valid fields are {}, got {} (type: {})").format(
                            func_name, invalid_fields, repr(valid_fields), fields, type(fields)
                        ))
                return

            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, expect a string or a list of string, got {} (type: {})").format(
                    func_name, self._arg_name, repr(fields), type(fields)
                ))

        self._rules.append(check_are_valid_fields)
        return self

    def _are_valid_instruments(self, func_name, values):
        if isinstance(values, (six.string_types, Instrument)):
            self._is_valid_instrument(func_name, values)
        elif isinstance(values, list):
            for v in values:
                self._is_valid_instrument(func_name, v)
        else:
            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, expect a string or a list of string, got {} (type: {})").format(
                    func_name, self._arg_name, repr(values), type(values)
                ))

    def are_valid_instruments(self, ignore_none=False):

        def check_are_valid_instruments(func_name, values):
            if values is None and ignore_none:
                return

            return self._are_valid_instruments(func_name, values)

        self._rules.append(check_are_valid_instruments)
        return self

    def is_valid_date(self, ignore_none=True):
        def check_is_valid_date(func_name, value):
            if ignore_none and value is None:
                return None
            if isinstance(value, (datetime.date, pd.Timestamp)):
                return
            if isinstance(value, six.string_types):
                try:
                    v = parse_date(value)
                    return
                except ValueError:
                    raise RQInvalidArgument(
                        _(u"function {}: invalid {} argument, expect a valid date, got {} (type: {})").format(
                            func_name, self._arg_name, value, type(value)
                        ))

            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, expect a valid date, got {} (type: {})").format(
                    func_name, self._arg_name, value, type(value)
                ))

        self._rules.append(check_is_valid_date)
        return self

    def is_greater_or_equal_than(self, low):
        def check_greater_or_equal_than(func_name, value):
            if isinstance(value, (int, float)) and value < low:
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, expect a value >= {}, got {} (type: {})").format(
                        func_name, self._arg_name, low, value, type(value)
                    ))
        self._rules.append(check_greater_or_equal_than)
        return self

    def is_greater_than(self, low):
        def check_greater_than(func_name, value):
            if isinstance(value, (int, float)) and value <= low:
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, expect a value > {}, got {} (type: {})").format(
                        func_name, self._arg_name, low, value, type(value)
                    ))
        self._rules.append(check_greater_than)
        return self

    def is_less_or_equal_than(self, high):
        def check_less_or_equal_than(func_name, value):
            if isinstance(value, (int, float)) and value > high:
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, expect a value <= {}, got {} (type: {})").format(
                        func_name, self._arg_name, high, value, type(value)
                    ))

        self._rules.append(check_less_or_equal_than)
        return self

    def is_less_than(self, high):
        def check_less_than(func_name, value):
            if isinstance(value, (int, float)) and value >= high:
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, expect a value < {}, got {} (type: {})").format(
                        func_name, self._arg_name, high, value, type(value)
                    ))

        self._rules.append(check_less_than)
        return self

    def _is_valid_interval(self, func_name, value):
        valid = isinstance(value, six.string_types) and value[-1] in {'d', 'm', 'q', 'y'}
        if valid:
            try:
                valid = int(value[:-1]) > 0
            except (ValueError, TypeError):
                valid = False

        if not valid:
            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, interval should be in form of '1d', '3m', '4q', '2y', "
                  u"got {} (type: {})").format(
                    func_name, self.arg_name, value, type(value)
                ))

    def is_valid_interval(self):
        self._rules.append(self._is_valid_interval)
        return self

    def _is_valid_quarter(self, func_name, value):
        if value is None:
            valid = True
        else:
            valid = isinstance(value, six.string_types) and value[-2] == 'q'
            if valid:
                try:
                    valid =  1990 <= int(value[:-2]) <= 2099 and 1 <= int(value[-1]) <= 4
                except (ValueError, TypeError):
                    valid = False

        if not valid:
            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, quarter should be in form of '2012q3', "
                  u"got {} (type: {})").format(
                    func_name, self.arg_name, value, type(value)
                ))

    def is_valid_quarter(self):
        self._rules.append(self._is_valid_quarter)
        return self

    def _are_valid_query_entities(self, func_name, entities):
        from sqlalchemy.orm.attributes import InstrumentedAttribute
        for e in entities:
            if not isinstance(e, InstrumentedAttribute):
                raise RQInvalidArgument(
                    _(u"function {}: invalid {} argument, should be entity like "
                      u"Fundamentals.balance_sheet.total_equity, got {} (type: {})").format(
                        func_name, self.arg_name, e, type(e)
                    ))

    def are_valid_query_entities(self):
        self._rules.append(self._are_valid_query_entities)
        return self

    def _is_valid_frequency(self, func_name, value):
        valid = isinstance(value, six.string_types) and value[-1] in ("d", "m", "w")
        if valid:
            try:
                valid = int(value[:-1]) > 0
            except (ValueError, TypeError):
                valid = False

        if not valid:
            raise RQInvalidArgument(
                _(u"function {}: invalid {} argument, frequency should be in form of "
                  u"'1m', '5m', '1d', '1w' got {} (type: {})").format(
                    func_name, self.arg_name, value, type(value)
                ))

    def is_valid_frequency(self):
        self._rules.append(self._is_valid_frequency)
        return self

    def verify(self, func_name, call_args):
        value = call_args[self.arg_name]
        for r in self._rules:
            r(func_name, value)


class ArgumentConverter(ArgumentCheckerBase):
    """验证参数并转换参数值，转换后的值会替换原参数"""
    def __init__(self, arg_name):
        super().__init__(arg_name)

    def is_listed_instrument(self):
        """验证并转换为上市中的 Instrument 对象"""
        self._rules.append(lambda func_name, value: assure_listed_instrument(value))
        return self

    def convert(self, func_name, call_args):
        """执行转换规则，返回转换后的值"""
        value = call_args[self.arg_name]
        for r in self._rules:
            value = r(func_name, value)
        return value


def verify_that(arg_name, pre_check=False):
    return ArgumentChecker(arg_name, pre_check)


def assure_that(arg_name):
    return ArgumentConverter(arg_name)


def get_call_args(func, args, kwargs, traceback=None):
    try:
        return inspect.getcallargs(unwrapper(func), *args, **kwargs)
    except TypeError as e:
        six.reraise(RQTypeError, RQTypeError(*e.args), traceback)


class ApiArgumentsChecker(object):
    def __init__(self, rules: Iterable[ArgumentCheckerBase]):
        self._checkers: List[ArgumentChecker] = []
        self._converters: List[ArgumentConverter] = []
        for r in rules:
            if isinstance(r, ArgumentConverter):
                self._converters.append(r)
            elif isinstance(r, ArgumentChecker):
                self._checkers.append(r)

    @property
    def pre_check_rules(self):
        for r in self._checkers:
            if r.pre_check:
                yield r

    @property
    def post_check_rules(self):
        for r in self._checkers:
            if not r.pre_check:
                yield r

    def _apply_checkers(self, checkers: Iterable[ArgumentChecker], func_name: str, get_call_args: Callable[[], Dict[str, Any]]):
        if not checkers:
            return
        # lazy evaluate call_args, avoid unnecessary evaluation
        call_args = get_call_args()
        for r in checkers:
            r.verify(func_name, call_args)

    def _apply_converters(self, func_name: str, get_call_args: Callable[[], Dict[str, Any]]):
        """应用所有转换器，返回转换后的参数字典"""
        converted = {}
        if not self._converters:
            return converted
        # lazy evaluate call_args, avoid unnecessary evaluation
        call_args = get_call_args()
        for converter in self._converters:
            converted[converter.arg_name] = converter.convert(func_name, call_args)
        return converted

    @contextmanager
    def check(self, func, args, kwargs):
        _call_args = None
        def call_args():
            nonlocal _call_args
            if _call_args is None:
                _call_args = get_call_args(func, args, kwargs)
            return _call_args

        self._apply_checkers(self.pre_check_rules, func.__name__, call_args)
        converted_args = self._apply_converters(func.__name__, call_args)
        if converted_args:
            updated_kwargs = call_args()
            updated_kwargs.update(converted_args)
        else:
            updated_kwargs = None
        try:
            yield updated_kwargs
        except RQInvalidArgument:
            raise
        except Exception as e:
            exc_info = sys.exc_info()
            t, v, tb = exc_info

            try:
                self._apply_checkers(self.post_check_rules, func.__name__, call_args)
            except RQInvalidArgument as e:
                six.reraise(RQInvalidArgument, e, tb)
                return

            if getattr(e, EXC_EXT_NAME, EXC_TYPE.NOTSET) == EXC_TYPE.NOTSET:
                patch_system_exc(e)

            raise


def apply_rules(*rules):
    checker = ApiArgumentsChecker(rules)

    def decorator(func):
        @wraps(func)
        def api_rule_check_wrapper(*args, **kwargs):
            with checker.check(func, args, kwargs) as update_kwargs:
                # 将转换后的参数注入 kwargs
                if update_kwargs:                
                    return func(**update_kwargs)
                else:
                    return func(*args, **kwargs)

        setattr(api_rule_check_wrapper, "_rq_exception_checked", True)
        return api_rule_check_wrapper

    return decorator
