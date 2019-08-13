# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from __future__ import division

import datetime
import inspect
import sys
import types
from collections import Iterable
from functools import wraps
from types import FunctionType

import pandas as pd
import numpy as np
import six
from dateutil.parser import parse

from rqalpha.api import names
from rqalpha.environment import Environment
from rqalpha.execution_context import ExecutionContext
from rqalpha.utils import to_industry_code, to_sector_name, unwrapper, is_valid_price
from rqalpha.utils.exception import (
    patch_user_exc,
    patch_system_exc,
    EXC_EXT_NAME,
    RQInvalidArgument,
)
from rqalpha.utils.i18n import gettext as _

# noinspection PyUnresolvedReferences
from rqalpha.utils.logger import user_log as logger
from rqalpha.utils.logger import user_system_log

from rqalpha.model.instrument import SectorCodeItem, IndustryCodeItem
from rqalpha.utils.arg_checker import apply_rules, verify_that

# noinspection PyUnresolvedReferences
from rqalpha.model.instrument import (
    Instrument,
    SectorCode as sector_code,
    IndustryCode as industry_code,
)

# noinspection PyUnresolvedReferences
from rqalpha.const import (
    EXECUTION_PHASE,
    EXC_TYPE,
    ORDER_STATUS,
    SIDE,
    POSITION_EFFECT,
    ORDER_TYPE,
    MATCHING_TYPE,
    RUN_TYPE,
    POSITION_DIRECTION,
)

# noinspection PyUnresolvedReferences
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle

# noinspection PyUnresolvedReferences
from rqalpha.events import EVENT

__all__ = [
    "logger",
    "sector_code",
    "industry_code",
    "LimitOrder",
    "MarketOrder",
    "ORDER_STATUS",
    "SIDE",
    "POSITION_EFFECT",
    "POSITION_DIRECTION",
    "ORDER_TYPE",
    "RUN_TYPE",
    "MATCHING_TYPE",
    "EVENT",
]


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


def export_as_api(func):
    __all__.append(func.__name__)

    if isinstance(func, FunctionType):
        func = decorate_api_exc(func)
    globals()[func.__name__] = func

    return func


def assure_order_book_id(id_or_ins):
    if isinstance(id_or_ins, Instrument):
        order_book_id = id_or_ins.order_book_id
    elif isinstance(id_or_ins, six.string_types):
        order_book_id = (
            Environment.get_instance().data_proxy.instruments(id_or_ins).order_book_id
        )
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))

    return order_book_id


def cal_style(price, style):
    if price is None and style is None:
        return MarketOrder()

    if style is not None:
        if not isinstance(style, OrderStyle):
            raise RuntimeError
        return style

    if isinstance(price, OrderStyle):
        # 为了 order_xxx('RB1710', 10, MarketOrder()) 这种写法
        if isinstance(price, LimitOrder):
            if np.isnan(price.get_limit_price()):
                raise RQInvalidArgument(_(u"Limit order price should not be nan."))
        return price

    if np.isnan(price):
        raise RQInvalidArgument(_(u"Limit order price should not be nan."))

    return LimitOrder(price)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
def get_order(order):
    return order


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
def get_open_orders():
    """
    获取当日未成交订单数据

    :return: List[:class:`~Order` object]
    """
    return Environment.get_instance().broker.get_open_orders()


@export_as_api
@apply_rules(
    verify_that("id_or_ins").is_valid_instrument(),
    verify_that("amount").is_number().is_greater_than(0),
    verify_that("side").is_in([SIDE.BUY, SIDE.SELL]),
)
def submit_order(id_or_ins, amount, side, price=None, position_effect=None):
    """
    通用下单函数，策略可以通过该函数自由选择参数下单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param float amount: 下单量，需为正数

    :param side: 多空方向，多（SIDE.BUY）或空（SIDE.SELL）
    :type side: :class:`~SIDE` enum

    :param float price: 下单价格，默认为None，表示市价单

    :param position_effect: 开平方向，开仓（POSITION_EFFECT.OPEN），平仓（POSITION.CLOSE）或平今（POSITION_EFFECT.CLOSE_TODAY），交易股票不需要该参数
    :type position_effect: :class:`~POSITION_EFFECT` enum

    :return: :class:`~Order` object | None

    :example:

    .. code-block:: python

        # 购买 2000 股的平安银行股票，并以市价单发送：
        submit_order('000001.XSHE', 2000, SIDE.BUY)
        # 平 10 份 RB1812 多方向的今仓，并以 4000 的价格发送限价单
        submit_order('RB1812', 10, SIDE.SELL, price=4000, position_effect=POSITION_EFFECT.CLOSE_TODAY)

    """
    order_book_id = assure_order_book_id(id_or_ins)
    env = Environment.get_instance()
    if (
        env.config.base.run_type != RUN_TYPE.BACKTEST
        and env.get_instrument(order_book_id).type == "Future"
    ):
        if "88" in order_book_id:
            raise RQInvalidArgument(
                _(u"Main Future contracts[88] are not supported in paper trading.")
            )
        if "99" in order_book_id:
            raise RQInvalidArgument(
                _(u"Index Future contracts[99] are not supported in paper trading.")
            )
    style = cal_style(price, None)
    market_price = env.get_last_price(order_book_id)
    if not is_valid_price(market_price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(
                order_book_id=order_book_id
            )
        )
        return

    amount = int(amount)

    order = Order.__from_create__(
        order_book_id=order_book_id,
        quantity=amount,
        side=side,
        style=style,
        position_effect=position_effect,
    )

    if order.type == ORDER_TYPE.MARKET:
        order.set_frozen_price(market_price)
    if env.can_submit_order(order):
        env.broker.submit_order(order)
        return order


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL,
)
@apply_rules(verify_that("order").is_instance_of(Order))
def cancel_order(order):
    """
    撤单

    :param order: 需要撤销的order对象
    :type order: :class:`~Order` object
    """
    env = Environment.get_instance()
    if env.can_cancel_order(order):
        env.broker.cancel_order(order)
    return order


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def update_universe(id_or_symbols):
    """
    该方法用于更新现在关注的证券的集合（e.g.：股票池）。PS：会在下一个bar事件触发时候产生（新的关注的股票池更新）效果。并且update_universe会是覆盖（overwrite）的操作而不是在已有的股票池的基础上进行增量添加。比如已有的股票池为['000001.XSHE', '000024.XSHE']然后调用了update_universe(['000030.XSHE'])之后，股票池就会变成000030.XSHE一个股票了，随后的数据更新也只会跟踪000030.XSHE这一个股票了。

    :param id_or_symbols: 标的物
    :type id_or_symbols: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
    if isinstance(id_or_symbols, (six.string_types, Instrument)):
        id_or_symbols = [id_or_symbols]
    order_book_ids = set(
        assure_order_book_id(order_book_id) for order_book_id in id_or_symbols
    )
    if order_book_ids != Environment.get_instance().get_universe():
        Environment.get_instance().update_universe(order_book_ids)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def subscribe(id_or_symbols):
    """
    订阅合约行情。该操作会导致合约池内合约的增加，从而影响handle_bar中处理bar数据的数量。

    需要注意，用户在初次编写策略时候需要首先订阅合约行情，否则handle_bar不会被触发。

    :param id_or_symbols: 标的物
    :type id_or_symbols: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
    current_universe = Environment.get_instance().get_universe()
    if isinstance(id_or_symbols, six.string_types):
        order_book_id = instruments(id_or_symbols).order_book_id
        current_universe.add(order_book_id)
    elif isinstance(id_or_symbols, Instrument):
        current_universe.add(id_or_symbols.order_book_id)
    elif isinstance(id_or_symbols, Iterable):
        for item in id_or_symbols:
            current_universe.add(assure_order_book_id(item))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))
    verify_that("id_or_symbols")._are_valid_instruments("subscribe", id_or_symbols)
    Environment.get_instance().update_universe(current_universe)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def unsubscribe(id_or_symbols):
    """
    取消订阅合约行情。取消订阅会导致合约池内合约的减少，如果当前合约池中没有任何合约，则策略直接退出。

    :param id_or_symbols: 标的物
    :type id_or_symbols: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]
    """
    current_universe = Environment.get_instance().get_universe()
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
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))

    Environment.get_instance().update_universe(current_universe)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("date").is_valid_date(ignore_none=True),
    verify_that("tenor").is_in(names.VALID_TENORS, ignore_none=True),
)
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
    env = Environment.get_instance()
    trading_date = env.trading_dt.date()
    yesterday = env.data_proxy.get_previous_trading_date(trading_date)

    if date is None:
        date = yesterday
    else:
        date = pd.Timestamp(date)
        if date > yesterday:
            raise RQInvalidArgument(
                "get_yield_curve: {} >= now({})".format(date, yesterday)
            )

    return env.data_proxy.get_yield_curve(start_date=date, end_date=date, tenor=tenor)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("order_book_id").is_valid_instrument(),
    verify_that("bar_count").is_instance_of(int).is_greater_than(0),
    verify_that("frequency").is_valid_frequency(),
    verify_that("fields").are_valid_fields(
        names.VALID_HISTORY_FIELDS, ignore_none=True
    ),
    verify_that("skip_suspended").is_instance_of(bool),
    verify_that("include_now").is_instance_of(bool),
    verify_that("adjust_type").is_in({"pre", "none", "post"}),
)
def history_bars(
    order_book_id,
    bar_count,
    frequency,
    fields=None,
    skip_suspended=True,
    include_now=False,
    adjust_type="pre",
):
    """
    获取指定合约的历史行情，同时支持日以及分钟历史数据。不能在init中调用。

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

    :param order_book_id: 合约代码
    :type order_book_id: `str`

    :param int bar_count: 获取的历史数据数量，必填项
    :param str frequency: 获取数据什么样的频率进行。'1d'或'1m'分别表示每日和每分钟，必填项
    :param str fields: 返回数据字段。必填项。见下方列表。
    :param bool skip_suspended: 是否跳过停牌数据
    :param bool include_now: 是否包含当前数据
    :param str adjust_type: 复权类型，默认为前复权 pre；可选 pre, none, post

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
    open_interest               持仓量（期货专用）
    basis_spread                期现差（股指期货专用）
    settlement                  结算价（期货日线专用）
    prev_settlement             结算价（期货日线专用）
    =========================   ===================================================

    :return: `ndarray`

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
    env = Environment.get_instance()
    dt = env.calendar_dt

    if frequency[-1] not in {"m", "d"}:
        raise RQInvalidArgument("invalid frequency {}".format(frequency))

    if frequency[-1] == "m" and env.config.base.frequency == "1d":
        raise RQInvalidArgument("can not get minute history in day back test")

    if frequency[-1] == "d" and frequency != "1d":
        raise RQInvalidArgument("invalid frequency")

    if adjust_type not in {"pre", "post", "none"}:
        raise RuntimeError("invalid adjust_type")

    if frequency == "1d":
        sys_frequency = Environment.get_instance().config.base.frequency
        if (
            sys_frequency in ["1m", "tick"]
            and not include_now
            and ExecutionContext.phase() != EXECUTION_PHASE.AFTER_TRADING
        ) or (ExecutionContext.phase() == EXECUTION_PHASE.BEFORE_TRADING):
            dt = env.data_proxy.get_previous_trading_date(env.trading_dt.date())
            # 当 EXECUTION_PHASE.BEFORE_TRADING 的时候，强制 include_now 为 False
            include_now = False
        if sys_frequency == "1d":
            # 日回测不支持 include_now
            include_now = False

    if fields is None:
        fields = ["datetime", "open", "high", "low", "close", "volume"]

    return env.data_proxy.history_bars(
        order_book_id,
        bar_count,
        frequency,
        fields,
        dt,
        skip_suspended=skip_suspended,
        include_now=include_now,
        adjust_type=adjust_type,
        adjust_orig=env.trading_dt,
    )


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("type").are_valid_fields(
        names.VALID_INSTRUMENT_TYPES, ignore_none=True
    ),
    verify_that("date").is_valid_date(ignore_none=True),
)
def all_instruments(type=None, date=None):
    """
    获取某个国家市场的所有合约信息。使用者可以通过这一方法很快地对合约信息有一个快速了解，目前仅支持中国市场。

    :param str type: 需要查询合约类型，例如：type='CS'代表股票。默认是所有类型

    :param date: 查询时间点
    :type date: `str` | `datetime` | `date`


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
    env = Environment.get_instance()
    if date is None:
        dt = env.trading_dt
    else:
        dt = pd.Timestamp(date).to_pydatetime()
        dt = min(dt, env.trading_dt)

    if type is not None:
        if isinstance(type, six.string_types):
            type = [type]

        types = set()
        for t in type:
            if t == "Stock":
                types.add("CS")
            elif t == "Fund":
                types.update(["ETF", "LOF", "SF", "FenjiA", "FenjiB", "FenjiMu"])
            else:
                types.add(t)
    else:
        types = None

    result = env.data_proxy.all_instruments(types, dt)
    if types is not None and len(types) == 1:
        return pd.DataFrame([i.__dict__ for i in result])

    return pd.DataFrame(
        [
            [i.order_book_id, i.symbol, i.type, i.listed_date, i.de_listed_date]
            for i in result
        ],
        columns=["order_book_id", "symbol", "type", "listed_date", "de_listed_date"],
    )


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").is_instance_of((str, Iterable)))
def instruments(id_or_symbols):
    """
    获取某个国家市场内一个或多个合约的详细信息。目前仅支持中国市场。

    :param id_or_symbols: 合约代码或者合约代码列表
    :type id_or_symbols: `str` | List[`str`]

    :return: :class:`~Instrument`

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
    return Environment.get_instance().data_proxy.instruments(id_or_symbols)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("code").is_instance_of((str, SectorCodeItem)))
def sector(code):
    """
    获得属于某一板块的所有股票列表。

    :param code: 板块名称或板块代码。例如，能源板块可填写'Energy'、'能源'或sector_code.Energy
        :type code: `str` | `sector_code`

    :return: list of order_book_id 属于该板块的股票列表

    目前支持的板块分类如下，其取值参考自MSCI发布的全球行业标准分类:

    =========================   =========================   ==============================================================================
    板块代码                      中文板块名称                  英文板块名称
    =========================   =========================   ==============================================================================
    Energy                      能源                         energy
    Materials                   原材料                        materials
    ConsumerDiscretionary       非必需消费品                   consumer discretionary
    ConsumerStaples             必需消费品                    consumer staples
    HealthCare                  医疗保健                      health care
    Financials                  金融                         financials
    InformationTechnology       信息技术                      information technology
    TelecommunicationServices   电信服务                      telecommunication services
    Utilities                   公共服务                      utilities
    Industrials                 工业                         industrials
    =========================   =========================   ==============================================================================

    :example:

    ..  code-block:: python3
        :linenos:

        def init(context):
            ids1 = sector("consumer discretionary")
            ids2 = sector("非必需消费品")
            ids3 = sector("ConsumerDiscretionary")
            assert ids1 == ids2 and ids1 == ids3
            logger.info(ids1)
        #INIT INFO
        #['002045.XSHE', '603099.XSHG', '002486.XSHE', '002536.XSHE', '300100.XSHE', '600633.XSHG', '002291.XSHE', ..., '600233.XSHG']
    """
    if not isinstance(code, six.string_types):
        code = code.name
    else:
        code = to_sector_name(code)

    return Environment.get_instance().data_proxy.sector(code)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("code").is_instance_of((str, IndustryCodeItem)))
def industry(code):
    """
    获得属于某一行业的所有股票列表。

    :param str code: 行业名称或行业代码。例如，农业可填写industry_code.A01 或 'A01'

    :return: list of order_book_id 获得属于某一行业的所有股票

    我们目前使用的行业分类来自于中国国家统计局的 `国民经济行业分类 <http://www.stats.gov.cn/tjsj/tjbz/hyflbz/>`_ ，可以使用这里的任何一个行业代码来调用行业的股票列表：

    =========================   ===================================================
    行业代码                      行业名称
    =========================   ===================================================
    A01                         农业
    A02                         林业
    A03                         畜牧业
    A04                         渔业
    A05                         农、林、牧、渔服务业
    B06                         煤炭开采和洗选业
    B07                         石油和天然气开采业
    B08                         黑色金属矿采选业
    B09                         有色金属矿采选业
    B10                         非金属矿采选业
    B11                         开采辅助活动
    B12                         其他采矿业
    C13                         农副食品加工业
    C14                         食品制造业
    C15                         酒、饮料和精制茶制造业
    C16                         烟草制品业
    C17                         纺织业
    C18                         纺织服装、服饰业
    C19                         皮革、毛皮、羽毛及其制品和制鞋业
    C20                         木材加工及木、竹、藤、棕、草制品业
    C21                         家具制造业
    C22                         造纸及纸制品业
    C23                         印刷和记录媒介复制业
    C24                         文教、工美、体育和娱乐用品制造业
    C25                         石油加工、炼焦及核燃料加工业
    C26                         化学原料及化学制品制造业
    C27                         医药制造业
    C28                         化学纤维制造业
    C29                         橡胶和塑料制品业
    C30                         非金属矿物制品业
    C31                         黑色金属冶炼及压延加工业
    C32                         有色金属冶炼和压延加工业
    C33                         金属制品业
    C34                         通用设备制造业
    C35                         专用设备制造业
    C36                         汽车制造业
    C37                         铁路、船舶、航空航天和其它运输设备制造业
    C38                         电气机械及器材制造业
    C39                         计算机、通信和其他电子设备制造业
    C40                         仪器仪表制造业
    C41                         其他制造业
    C42                         废弃资源综合利用业
    C43                         金属制品、机械和设备修理业
    D44                         电力、热力生产和供应业
    D45                         燃气生产和供应业
    D46                         水的生产和供应业
    E47                         房屋建筑业
    E48                         土木工程建筑业
    E49                         建筑安装业
    E50                         建筑装饰和其他建筑业
    F51                         批发业
    F52                         零售业
    G53                         铁路运输业
    G54                         道路运输业
    G55                         水上运输业
    G56                         航空运输业
    G57                         管道运输业
    G58                         装卸搬运和运输代理业
    G59                         仓储业
    G60                         邮政业
    H61                         住宿业
    H62                         餐饮业
    I63                         电信、广播电视和卫星传输服务
    I64                         互联网和相关服务
    I65                         软件和信息技术服务业
    J66                         货币金融服务
    J67                         资本市场服务
    J68                         保险业
    J69                         其他金融业
    K70                         房地产业
    L71                         租赁业
    L72                         商务服务业
    M73                         研究和试验发展
    M74                         专业技术服务业
    M75                         科技推广和应用服务业
    N76                         水利管理业
    N77                         生态保护和环境治理业
    N78                         公共设施管理业
    O79                         居民服务业
    O80                         机动车、电子产品和日用产品修理业
    O81                         其他服务业
    P82                         教育
    Q83                         卫生
    Q84                         社会工作
    R85                         新闻和出版业
    R86                         广播、电视、电影和影视录音制作业
    R87                         文化艺术业
    R88                         体育
    R89                         娱乐业
    S90                         综合
    =========================   ===================================================

    :example:

    ..  code-block:: python3
        :linenos:

        def init(context):
            stock_list = industry('A01')
            logger.info("农业股票列表：" + str(stock_list))

        #INITINFO 农业股票列表：['600354.XSHG', '601118.XSHG', '002772.XSHE', '600371.XSHG', '600313.XSHG', '600672.XSHG', '600359.XSHG', '300143.XSHE', '002041.XSHE', '600762.XSHG', '600540.XSHG', '300189.XSHE', '600108.XSHG', '300087.XSHE', '600598.XSHG', '000998.XSHE', '600506.XSHG']

    """
    if not isinstance(code, six.string_types):
        code = code.code
    else:
        code = to_industry_code(code)

    return Environment.get_instance().data_proxy.industry(code)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("start_date").is_valid_date(ignore_none=False),
    verify_that("end_date").is_valid_date(ignore_none=False),
)
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
    return Environment.get_instance().data_proxy.get_trading_dates(start_date, end_date)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("date").is_valid_date(ignore_none=False),
    verify_that("n").is_instance_of(int).is_greater_or_equal_than(1),
)
def get_previous_trading_date(date, n=1):
    """
    获取指定日期的之前的第 n 个交易日。

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`
    :param n:

    :return: `datetime.date`

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_previous_trading_date(date='2016-05-02')
        [Out]
        [datetime.date(2016, 4, 29)]
    """
    return Environment.get_instance().data_proxy.get_previous_trading_date(date, n)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("date").is_valid_date(ignore_none=False),
    verify_that("n").is_instance_of(int).is_greater_or_equal_than(1),
)
def get_next_trading_date(date, n=1):
    """
    获取指定日期之后的第 n 个交易日

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`
    :param n:

    :return: `datetime.date`

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_next_trading_date(date='2016-05-01')
        [Out]
        [datetime.date(2016, 5, 3)]
    """
    return Environment.get_instance().data_proxy.get_next_trading_date(date, n)


def to_date(date):
    if isinstance(date, six.string_types):
        return parse(date).date()

    if isinstance(date, datetime.datetime):
        try:
            return date.date()
        except AttributeError:
            return date

    raise RQInvalidArgument("unknown date value: {}".format(date))


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("order_book_id").is_valid_instrument(),
    verify_that("start_date").is_valid_date(ignore_none=False),
)
def get_dividend(order_book_id, start_date):
    """
    获取某只股票到策略当前日期前一天的分红情况（包含起止日期）。

    :param order_book_id: 股票代码
    :type order_book_id: str
    :param start_date: 开始日期，需要早于策略当前日期
    :type start_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: ndarray

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    announcement_date           分红宣布日
    book_closure_date           股权登记日
    dividend_cash_before_tax    税前分红
    ex_dividend_date            除权除息日
    payable_date                分红到帐日
    round_lot                   分红最小单位
    =========================   ===================================================
    """
    # adjusted 参数在不复权数据回测时不再提供
    env = Environment.get_instance()
    dt = env.trading_dt.date() - datetime.timedelta(days=1)
    start_date = to_date(start_date)
    if start_date > dt:
        raise RQInvalidArgument(
            _(
                u"in get_dividend, start_date {} is later than the previous test day {}"
            ).format(start_date, dt)
        )
    order_book_id = assure_order_book_id(order_book_id)
    array = env.data_proxy.get_dividend(order_book_id)
    if array is None:
        return None

    sd = start_date.year * 10000 + start_date.month * 100 + start_date.day
    ed = dt.year * 10000 + dt.month * 100 + dt.day
    return array[
        (array["announcement_date"] >= sd) & (array["announcement_date"] <= ed)
    ]


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_BAR, EXECUTION_PHASE.ON_TICK, EXECUTION_PHASE.SCHEDULED
)
@apply_rules(
    verify_that("series_name", pre_check=True).is_instance_of(str),
    verify_that("value", pre_check=True).is_number(),
)
def plot(series_name, value):
    """
    在生成的图标结果中，某一个根线上增加一个点。

    :param str series_name: 序列名称
    :param float value: 值
    """
    Environment.get_instance().add_plot(series_name, value)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbol").is_valid_instrument())
def current_snapshot(id_or_symbol):
    """
    获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。
    市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。
    在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。
    需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。
    如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

    :param str id_or_symbol: 合约代码或简称

    :return: :class:`~Tick`

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
    env = Environment.get_instance()
    frequency = env.config.base.frequency
    order_book_id = assure_order_book_id(id_or_symbol)

    dt = env.calendar_dt

    if env.config.base.run_type == RUN_TYPE.BACKTEST:
        if ExecutionContext.phase() == EXECUTION_PHASE.BEFORE_TRADING:
            dt = env.data_proxy.get_previous_trading_date(env.trading_dt.date())
            return env.data_proxy.current_snapshot(order_book_id, "1d", dt)
        elif ExecutionContext.phase() == EXECUTION_PHASE.AFTER_TRADING:
            return env.data_proxy.current_snapshot(order_book_id, "1d", dt)

    # PT、实盘直接取最新快照，忽略 frequency, dt 参数
    return env.data_proxy.current_snapshot(order_book_id, frequency, dt)


@export_as_api
def get_positions():
    """
    获取所有持仓信息

    :return: list BookingPosition

    :example:

    ..  code-block:: python3

        [In] get_positions()
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'today_quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0}),
         BookingPosition({'order_book_id': '000010.XSHE', 'quantity': 100, 'today_quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 0.0, 'avg_price': 3.09, 'last_price': 0, 'position_pnl': 0.0})]

    """
    booking = Environment.get_instance().booking
    if not booking:
        raise RuntimeError(
            _("Booking has not been set, please check your broker configuration.")
        )
    return booking.get_positions()


@export_as_api
@apply_rules(
    verify_that("direction").is_in([POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT])
)
def get_position(order_book_id, direction):
    """
    获取某个标的的持仓信息

    :param order_book_id: 标的编号
    :param direction: 持仓类型 “long_positions” | “short_positions” | “backward_trade_set”

    :return: list BookingPosition

    :example:

    ..  code-block:: python3

        [In] get_position('000014.XSHE','long_positions")
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'today_quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0})]

    """
    booking = Environment.get_instance().booking
    if not booking:
        raise RuntimeError(
            _("Booking has not been set, please check your broker configuration.")
        )

    return booking.get_position(order_book_id, direction)


@export_as_api
@apply_rules(
    verify_that("event_type").is_instance_of(EVENT),
    verify_that("handler").is_instance_of(types.FunctionType),
)
def subscribe_event(event_type, handler):
    """
    订阅框架内部事件，注册事件处理函数

    :param event_type: 事件类型
    :param handler: 处理函数

    :return: None

    :example:

    ..  code-block:: python3

        from rqalpha.events import EVENT
        subscribe_event(EVENT.POST_BAR, print)

    """
    env = Environment.get_instance()
    user_strategy = env.user_strategy
    env.event_bus.add_listener(
        event_type, user_strategy.wrap_user_event_handler(handler), user=True
    )
