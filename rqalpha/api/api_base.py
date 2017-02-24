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
from ..utils import to_industry_code, to_sector_name, unwrapper
from ..utils.exception import patch_user_exc, patch_system_exc, EXC_EXT_NAME
from ..utils.i18n import gettext as _
from ..model.snapshot import SnapshotObject
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_order(order_id):
    if isinstance(order_id, Order):
        return order_id
    else:
        return ExecutionContext.account.get_order(order_id)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_open_orders():
    """
    获取当日未成交订单数据

    :return: List[:class:`~Order` object]
    """
    return ExecutionContext.account.get_open_orders()


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def cancel_order(order):
    """
    撤单

    :param order: 需要撤销的order对象
    :type order: :class:`~Order` object
    """
    order = order if isinstance(order, Order) else get_order(order)
    if order is None:
        patch_user_exc(KeyError(_("Cancel order fail: invalid order id")))
    ExecutionContext.broker.cancel_order(order)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def update_universe(id_or_symbols):
    """
    该方法用于更新现在关注的证券的集合（e.g.：股票池）。PS：会在下一个bar事件触发时候产生（新的关注的股票池更新）效果。并且update_universe会是覆盖（overwrite）的操作而不是在已有的股票池的基础上进行增量添加。比如已有的股票池为['000001.XSHE', '000024.XSHE']然后调用了update_universe(['000030.XSHE'])之后，股票池就会变成000030.XSHE一个股票了，随后的数据更新也只会跟踪000030.XSHE这一个股票了。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
    if isinstance(id_or_symbols, (six.string_types, Instrument)):
        id_or_symbols = [id_or_symbols]
    order_book_ids = set(assure_order_book_id(order_book_id) for order_book_id in id_or_symbols)
    if order_book_ids != Environment.get_instance().universe:
        Environment.get_instance().update_universe(order_book_ids)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def subscribe(id_or_symbols):
    """
    订阅合约行情。该操作会导致合约池内合约的增加，从而影响handle_bar中处理bar数据的数量。

    需要注意，用户在初次编写策略时候需要首先订阅合约行情，否则handle_bar不会被触发。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').are_valid_instruments())
def unsubscribe(id_or_symbols):
    """
    取消订阅合约行情。取消订阅会导致合约池内合约的减少，如果当前合约池中没有任何合约，则策略直接退出。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=True),
             verify_that('tenor').is_in(names.VALID_TENORS, ignore_none=True))
def get_yield_curve(date=None, tenor=None):
    """
    获取某个国家市场指定日期的收益率曲线水平。

    数据为2002年至今的中债国债收益率曲线，来源于中央国债登记结算有限责任公司。

    :param date: 查询日期，默认为策略当前日期前一天
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :param str tenor: 标准期限，'0S' - 隔夜，'1M' - 1个月，'1Y' - 1年，默认为全部期限

    :return: `pandas.DataFrame` - 查询时间段内无风险收益率曲线

    :example:

    ..  code-block:: python3
        :linenos:

        [In]
        get_yield_curve('20130104')

        [Out]
                        0S      1M      2M      3M      6M      9M      1Y      2Y  \
        2013-01-04  0.0196  0.0253  0.0288  0.0279  0.0280  0.0283  0.0292  0.0310

                        3Y      4Y   ...        6Y      7Y      8Y      9Y     10Y  \
        2013-01-04  0.0314  0.0318   ...    0.0342  0.0350  0.0353  0.0357  0.0361
        ...
    """
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('bar_count').is_instance_of(int).is_greater_than(0),
             verify_that('frequency').is_in(('1m', '1d')),
             verify_that('fields').are_valid_fields(names.VALID_HISTORY_FIELDS, ignore_none=True),
             verify_that('skip_suspended').is_instance_of(bool))
def history_bars(order_book_id, bar_count, frequency, fields=None, skip_suspended=True):
    """
    获取指定合约的历史行情，同时支持日以及分钟历史数据。不能在init中调用。 注意，该API会自动跳过停牌数据。

    日回测获取分钟历史数据：不支持

    日回测获取日历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日day bar
    T日handle_bar                T日day bar
    =========================   ===================================================

    分钟回测获取日历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日day bar
    T日handle_bar                T-1日day bar
    =========================   ===================================================

    分钟回测获取分钟历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日最后一个minute bar
    T日handle_bar                T日当前minute bar
    =========================   ===================================================

    :param order_book_id: 合约代码或者合约代码列表
    :type order_book_id: `str`

    :param int bar_count: 获取的历史数据数量，必填项

    :param str frequency: 获取数据什么样的频率进行。'1d'或'1m'分别表示每日和每分钟，必填项

    :param str fields: 返回数据字段。必填项。见下方列表。

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    datetime                    时间戳
    open                        开盘价
    high                        最高价
    low                         最低价
    close                       收盘价
    volume                      成交量
    total_turnover              成交额
    datetime                    int类型时间戳
    open_interest               持仓量（期货专用）
    basis_spread                期现差（股指期货专用）
    settlement                  结算价（期货日线专用）
    prev_settlement             结算价（期货日线专用）
    =========================   ===================================================

    :return: `ndarray`, 方便直接与talib等计算库对接，效率较history返回的DataFrame更高。

    :example:

    获取最近5天的日线收盘价序列（策略当前日期为20160706）:

    ..  code-block:: python3
        :linenos:

        [In]
        logger.info(history_bars('000002.XSHE', 5, '1d', 'close'))
        [Out]
        [ 8.69  8.7   8.71  8.81  8.81]
    """
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('type').is_in(names.VALID_INSTRUMENT_TYPES, ignore_none=True))
def all_instruments(type=None):
    """
    获取某个国家市场的所有合约信息。使用者可以通过这一方法很快地对合约信息有一个快速了解，目前仅支持中国市场。

    :param str type: 需要查询合约类型，例如：type='CS'代表股票。默认是所有类型

    :return: `pandas DataFrame` 所有合约的基本信息。

    其中type参数传入的合约类型和对应的解释如下：

    =========================   ===================================================
    合约类型                      说明
    =========================   ===================================================
    CS                          Common Stock, 即股票
    ETF                         Exchange Traded Fund, 即交易所交易基金
    LOF                         Listed Open-Ended Fund，即上市型开放式基金
    FenjiMu                     Fenji Mu Fund, 即分级母基金
    FenjiA                      Fenji A Fund, 即分级A类基金
    FenjiB                      Fenji B Funds, 即分级B类基金
    INDX                        Index, 即指数
    Future                      Futures，即期货，包含股指、国债和商品期货
    hour                        int - option [1,4]
    minute                      int - option [1,240]
    =========================   ===================================================

    :example:

    获取中国市场所有分级基金的基础信息:

    ..  code-block:: python3
        :linenos:

        [In]all_instruments('FenjiA')
        [Out]
            abbrev_symbol    order_book_id    product    sector_code  symbol
        0    CYGA    150303.XSHE    null    null    华安创业板50A
        1    JY500A    150088.XSHE    null    null    金鹰500A
        2    TD500A    150053.XSHE    null    null    泰达稳健
        3    HS500A    150110.XSHE    null    null    华商500A
        4    QSAJ    150235.XSHE    null    null    鹏华证券A
        ...

    """
    return ExecutionContext.data_proxy.all_instruments(type)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbols').is_instance_of((str, Iterable)))
def instruments(id_or_symbols):
    """
    获取某个国家市场内一个或多个合约的详细信息。目前仅支持中国市场。

    :param order_book_id: 合约代码或者合约代码列表
    :type order_book_id: `str` | List[`str`]

    :return: :class:`~StockInstrument` | :class:`~FutureInstrument`

    目前系统并不支持跨国家市场的同时调用。传入 order_book_id list必须属于同一国家市场，不能混合着中美两个国家市场的order_book_id。

    :example:

    *   获取单一股票合约的详细信息:

        ..  code-block:: python3
            :linenos:

            [In]instruments('000001.XSHE')
            [Out]
            Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)

    *   获取多个股票合约的详细信息:

        ..  code-block:: python3
            :linenos:

            [In]instruments(['000001.XSHE', '000024.XSHE'])
            [Out]
            [Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active), Instrument(order_book_id=000024.XSHE, symbol=招商地产, abbrev_symbol=ZSDC, listed_date=19930607, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)]

    *   获取合约已上市天数:

        ..  code-block:: python
            :linenos:

            instruments('000001.XSHE').days_from_listed()

    *   获取合约距离到期天数:

        ..  code-block:: python
            :linenos:

            instruments('IF1701').days_to_expire()
    """
    return ExecutionContext.data_proxy.instruments(id_or_symbols)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('code').is_instance_of((str, SectorCodeItem)))
def sector(code):
    if not isinstance(code, six.string_types):
        code = code.name
    else:
        code = to_sector_name(code)

    return ExecutionContext.data_proxy.sector(code)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('code').is_instance_of((str, IndustryCodeItem)))
def industry(code):
    if not isinstance(code, six.string_types):
        code = code.code
    else:
        code = to_industry_code(code)

    return ExecutionContext.data_proxy.industry(code)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def concept(*concept_names):
    return ExecutionContext.data_proxy.concept(*concept_names)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('start_date').is_valid_date(ignore_none=False))
@apply_rules(verify_that('end_date').is_valid_date(ignore_none=False))
def get_trading_dates(start_date, end_date):
    """
    获取某个国家市场的交易日列表（起止日期加入判断）。目前仅支持中国市场。

    :param start_date: 开始日期
    :type start_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :param end_date: 结束如期
    :type end_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: list[`datetime.date`]

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_trading_dates(start_date='2016-05-05', end_date='20160505')
        [Out]
        [datetime.date(2016, 5, 5)]
    """
    return ExecutionContext.data_proxy.get_trading_dates(start_date, end_date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=False))
def get_previous_trading_date(date):
    """
    获取指定日期的上一交易日。

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `datetime.date`

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_previous_trading_date(date='2016-05-02')
        [Out]
        [datetime.date(2016, 4, 29)]
    """
    return ExecutionContext.data_proxy.get_previous_trading_date(date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=False))
def get_next_trading_date(date):
    """
    获取指定日期的下一交易日

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `datetime.date`

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_next_trading_date(date='2016-05-01')
        [Out]
        [datetime.date(2016, 5, 3)]
    """
    return ExecutionContext.data_proxy.get_next_trading_date(date)


def to_date(date):
    if isinstance(date, six.string_types):
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('start_date').is_valid_date(ignore_none=False),
             verify_that('adjusted').is_instance_of(bool))
def get_dividend(order_book_id, start_date, adjusted=True):
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
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('series_name').is_instance_of(str),
             verify_that('value').is_number())
def plot(series_name, value):
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


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_symbol').is_valid_instrument())
def current_snapshot(id_or_symbol):
    """
    获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

    :param str order_book_id: 合约代码或简称

    :return: :class:`~Snapshot`

    :example:

    在handle_bar中调用该函数，假设策略当前时间是20160104 09:33:

    ..  code-block:: python3
        :linenos:

        [In]
        logger.info(current_snapshot('000001.XSHE'))
        [Out]
        2016-01-04 09:33:00.00  INFO
        Snapshot(order_book_id: '000001.XSHE', datetime: datetime.datetime(2016, 1, 4, 9, 33), open: 10.0, high: 10.025, low: 9.9667, last: 9.9917, volume: 2050320, total_turnover: 20485195, prev_close: 9.99)
    """
    data_proxy = ExecutionContext.data_proxy
    cal_dt = ExecutionContext.get_current_calendar_dt()

    frequency = Environment.get_instance().config.base.frequency

    order_book_id = assure_order_book_id(id_or_symbol)
    return data_proxy.current_snapshot(order_book_id, frequency, cal_dt)
