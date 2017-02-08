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

'''
更多描述请见
https://www.ricequant.com/api/python/chn
'''

from __future__ import division
import sys
import datetime
import inspect
import pandas as pd
import six
from collections import Iterable
from dateutil.parser import parse
from types import FunctionType
from functools import wraps
from typing import List

from ..environment import Environment
from ..model.instrument import Instrument, SectorCode as sector_code, IndustryCode as industry_code
from ..model.instrument import SectorCodeItem, IndustryCodeItem
from ..execution_context import ExecutionContext
from ..const import EXECUTION_PHASE, EXC_TYPE, ORDER_STATUS, SIDE, POSITION_EFFECT, ORDER_TYPE, MATCHING_TYPE, RUN_TYPE
from ..utils import to_industry_code, to_sector_name
from ..utils.exception import patch_user_exc, patch_system_exc, EXC_EXT_NAME
from ..utils.i18n import gettext as _
from ..model.order import Order, MarketOrder, LimitOrder
from ..model.slippage import PriceRatioSlippage
from ..utils.arg_checker import apply_rules, verify_that
from . import names

__all__ = [
    'sector_code',
    'industry_code',
    'LimitOrder',
    'MarketOrder',
    'PriceRatioSlippage',
    'ORDER_STATUS',
    'SIDE',
    'POSITION_EFFECT',
    'ORDER_TYPE',
    'RUN_TYPE',
    'MATCHING_TYPE',
]


def decorate_api_exc(func):
    f = func
    exception_checked = False
    while True:
        if getattr(f, '_rq_exception_checked', False):
            exception_checked = True
            break

        f = getattr(f, '__wrapped__', None)
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
            except Exception as e:
                if isinstance(e, TypeError):
                    exc_info = sys.exc_info()
                    try:
                        ret = inspect.getcallargs(inspect.unwrap(func), *args, **kwargs)
                    except TypeError:
                        t, v, tb = exc_info
                        raise patch_user_exc(v.with_traceback(tb))

                if getattr(e, EXC_EXT_NAME, EXC_TYPE.NOTSET) == EXC_TYPE.NOTSET:
                    patch_system_exc(e)

                raise

        return deco
    return func


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


def assure_order_book_id(id_or_ins):
    if isinstance(id_or_ins, Instrument):
        order_book_id = id_or_ins.order_book_id
    elif isinstance(id_or_ins, six.string_types):
        order_book_id = instruments(id_or_ins).order_book_id
    else:
        raise patch_user_exc(KeyError(_("unsupported order_book_id type")))

    return order_book_id


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_order(order_id) -> "[Deprecated]":
    if isinstance(order_id, Order):
        return order_id
    else:
        return ExecutionContext.account.get_order(order_id)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_open_orders() -> "Order[]":
    return ExecutionContext.account.get_open_orders()


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def cancel_order(order_id):
    order = order_id if isinstance(order_id, Order) else get_order(order_id)
    if order is None:
        patch_user_exc(KeyError(_("Cancel order fail: invalid order id")))
    ExecutionContext.broker.cancel_order(order)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def update_universe(id_or_symbols) -> None:
    if isinstance(id_or_symbols, (six.string_types, Instrument)):
        id_or_symbols = [id_or_symbols]
    order_book_ids = set(assure_order_book_id(order_book_id) for order_book_id in id_or_symbols)
    if order_book_ids != Environment.get_instance().universe:
        Environment.get_instance().update_universe(order_book_ids)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def subscribe(id_or_symbols) -> None:
    current_universe = Environment.get_instance().universe
    if isinstance(id_or_symbols, six.string_types):
        order_book_id = instruments(id_or_symbols).order_book_id
        current_universe.add(order_book_id)
    elif isinstance(id_or_symbols, Instrument):
        current_universe.add(id_or_symbols.order_book_id)
    elif isinstance(id_or_symbols, Iterable):
        for item in id_or_symbols:
            current_universe.add(assure_order_book_id(item))
    else:
        raise patch_user_exc(KeyError(_("unsupported order_book_id type")))
    Environment.get_instance().update_universe(current_universe)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def unsubscribe(id_or_symbols) -> None:
    current_universe = Environment.get_instance().universe
    if isinstance(id_or_symbols, six.string_types):
        order_book_id = instruments(id_or_symbols).order_book_id
        current_universe.discard(order_book_id)
    elif isinstance(id_or_symbols, Instrument):
        current_universe.discard(id_or_symbols.order_book_id)
    elif isinstance(id_or_symbols, Iterable):
        for item in id_or_symbols:
            i = assure_order_book_id(item)
            current_universe.discard(i)
    else:
        raise patch_user_exc(KeyError(_("unsupported order_book_id type")))

    Environment.get_instance().update_universe(current_universe)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=True),
             verify_that('tenor').is_in(names.VALID_TENORS, ignore_none=True))
def get_yield_curve(date=None, tenor=None) -> "Float | Series":
    data_proxy = ExecutionContext.data_proxy
    dt = ExecutionContext.get_current_trading_dt().date()

    yesterday = data_proxy.get_previous_trading_date(dt)

    if date is None:
        date = yesterday
    else:
        date = pd.Timestamp(date)
        if date > yesterday:
            raise patch_user_exc(RuntimeError('get_yield_curve: {} >= now({})'.format(date, yesterday)))

    return data_proxy.get_yield_curve(start_date=date, end_date=date, tenor=tenor)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('bar_count').is_instance_of(int).is_greater_than(0),
             verify_that('frequency').is_in(('1m', '1d')),
             verify_that('fields').are_valid_fields(names.VALID_HISTORY_FIELDS, ignore_none=True),
             verify_that('skip_suspended').is_instance_of(bool))
def history_bars(order_book_id, bar_count, frequency, fields=None, skip_suspended=True) -> "NDArray":
    order_book_id = assure_order_book_id(order_book_id)
    data_proxy = ExecutionContext.data_proxy
    dt = ExecutionContext.get_current_calendar_dt()

    if frequency == '1m' and Environment.get_instance().config.base.frequency == '1d':
        raise patch_user_exc(ValueError('can not get minute history in day back test'))

    if (Environment.get_instance().config.base.frequency == '1m' and frequency == '1d') or \
            (frequency == '1d' and ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING):
        # 在分钟回测获取日线数据, 应该推前一天，这里应该使用 trading date
        dt = data_proxy.get_previous_trading_date(ExecutionContext.get_current_trading_dt().date())

    return data_proxy.history_bars(order_book_id, bar_count, frequency, fields, dt, skip_suspended)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('type').is_in(names.VALID_INSTRUMENT_TYPES, ignore_none=True))
def all_instruments(type=None) -> pd.DataFrame:
    return ExecutionContext.data_proxy.all_instruments(type)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').is_instance_of((str, Iterable)))
def instruments(id_or_symbols):
    return ExecutionContext.data_proxy.instruments(id_or_symbols)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('code').is_instance_of((str, SectorCodeItem)))
def sector(code) -> List[str]:
    if not isinstance(code, str):
        code = code.name
    else:
        code = to_sector_name(code)

    return ExecutionContext.data_proxy.sector(code)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('code').is_instance_of((str, IndustryCodeItem)))
def industry(code) -> List[str]:
    if not isinstance(code, str):
        code = code.code
    else:
        code = to_industry_code(code)

    return ExecutionContext.data_proxy.industry(code)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def concept(*concept_names) -> List[str]:
    return ExecutionContext.data_proxy.concept(*concept_names)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('start_date').is_valid_date(ignore_none=False))
@apply_rules(verify_that('end_date').is_valid_date(ignore_none=False))
def get_trading_dates(start_date, end_date) -> List[datetime.datetime]:
    return ExecutionContext.data_proxy.get_trading_dates(start_date, end_date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=False))
def get_previous_trading_date(date) -> datetime.datetime:
    return ExecutionContext.data_proxy.get_previous_trading_date(date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=False))
def get_next_trading_date(date) -> datetime.datetime:
    return ExecutionContext.data_proxy.get_next_trading_date(date)


def to_date(date):
    if isinstance(date, str):
        return parse(date).date()

    if isinstance(date, datetime.date):
        try:
            return date.date()
        except AttributeError:
            return date

    raise patch_user_exc(ValueError('unknown date value: {}'.format(date)))


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('start_date').is_valid_date(ignore_none=False),
             verify_that('adjusted').is_instance_of(bool))
def get_dividend(order_book_id, start_date, adjusted=True) -> pd.DataFrame:
    dt = ExecutionContext.get_current_trading_dt().date() - datetime.timedelta(days=1)
    start_date = to_date(start_date)
    if start_date > dt:
        raise patch_user_exc(
            ValueError(_('in get_dividend, start_date {} is later than the previous test day {}').format(
                start_date, dt
            )))
    order_book_id = assure_order_book_id(order_book_id)
    df = ExecutionContext.data_proxy.get_dividend(order_book_id, adjusted)
    return df[start_date:dt]


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('series_name').is_instance_of(str),
             verify_that('value').is_number())
def plot(series_name, value) -> None:
    """
    Add a point to custom series.
    :param str series_name: the name of custom series
    :param float value: the value of the series in this time
    :return: None
    """
    if ExecutionContext.plots is None:
        # FIXME: this is ugly
        from ..utils.plot_store import PlotStore
        ExecutionContext.plots = PlotStore()
    ExecutionContext.plots.add_plot(ExecutionContext.trading_dt.date(), series_name, value)
