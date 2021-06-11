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

import types
from collections import Iterable
from datetime import date, datetime
from typing import Callable, List, Optional, Union

import pandas as pd
import numpy as np
import six

from rqalpha.apis import names
from rqalpha.environment import Environment
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.utils import is_valid_price
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.api import export_as_api
from rqalpha.utils.logger import user_log as logger, user_system_log, user_print
from rqalpha.model.instrument import Instrument
from rqalpha.model.tick import TickObject
from rqalpha.const import (
    EXECUTION_PHASE, ORDER_STATUS, SIDE, POSITION_EFFECT, ORDER_TYPE, MATCHING_TYPE, RUN_TYPE, POSITION_DIRECTION,
    DEFAULT_ACCOUNT_TYPE
)
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle
from rqalpha.core.events import EVENT, Event
from rqalpha.core.strategy_context import StrategyContext
from rqalpha.portfolio.position import Position

export_as_api(logger, name='logger')
export_as_api(user_print, name='print')
export_as_api(LimitOrder, name='LimitOrder')
export_as_api(MarketOrder, name='MarketOrder')
export_as_api(ORDER_STATUS, name='ORDER_STATUS')
export_as_api(SIDE, name='SIDE')
export_as_api(POSITION_EFFECT, name='POSITION_EFFECT')
export_as_api(POSITION_DIRECTION, name='POSITION_DIRECTION')
export_as_api(ORDER_TYPE, name='ORDER_TYPE')
export_as_api(RUN_TYPE, name='RUN_TYPE')
export_as_api(MATCHING_TYPE, name='MATCHING_TYPE')
export_as_api(EVENT, name='EVENT')


def assure_instrument(id_or_ins):
    if isinstance(id_or_ins, Instrument):
        return id_or_ins
    elif isinstance(id_or_ins, six.string_types):
        return Environment.get_instance().data_proxy.instruments(id_or_ins)
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))


def assure_order_book_id(id_or_ins):
    return assure_instrument(id_or_ins).order_book_id


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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
def get_open_orders():
    # type: () -> List[Order]
    """
    获取当日未成交订单数据
    """
    broker = Environment.get_instance().broker
    return [o for o in broker.get_open_orders() if o.position_effect != POSITION_EFFECT.EXERCISE]


@export_as_api
@apply_rules(
    verify_that("id_or_ins").is_valid_instrument(),
    verify_that("amount").is_number().is_greater_than(0),
    verify_that("side").is_in([SIDE.BUY, SIDE.SELL]),
)
def submit_order(id_or_ins, amount, side, price=None, position_effect=None):
    # type: (Union[str, Instrument], float, SIDE, Optional[float], Optional[POSITION_EFFECT]) -> Optional[Order]
    """
    通用下单函数，策略可以通过该函数自由选择参数下单。

    :param id_or_ins: 下单标的物
    :param amount: 下单量，需为正数
    :param side: 多空方向
    :param price: 下单价格，默认为None，表示市价单
    :param position_effect: 开平方向，交易股票不需要该参数
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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL,
)
@apply_rules(verify_that("order").is_instance_of(Order))
def cancel_order(order):
    # type: (Order) -> Order
    """
    撤单

    :param order: 需要撤销的order对象
    """
    env = Environment.get_instance()
    if env.can_cancel_order(order):
        env.broker.cancel_order(order)
    return order


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def update_universe(id_or_symbols):
    # type: (Union[str, Instrument, Iterable[str], Iterable[Instrument]]) -> None
    """
    该方法用于更新现在关注的证券的集合（e.g.：股票池）。PS：会在下一个bar事件触发时候产生（新的关注的股票池更新）效果。并且update_universe会是覆盖（overwrite）的操作而不是在已有的股票池的基础上进行增量添加。比如已有的股票池为['000001.XSHE', '000024.XSHE']然后调用了update_universe(['000030.XSHE'])之后，股票池就会变成000030.XSHE一个股票了，随后的数据更新也只会跟踪000030.XSHE这一个股票了。

    :param id_or_symbols: 标的物

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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def subscribe(id_or_symbols):
    # type: (Union[str, Instrument, Iterable[str], Iterable[Instrument]]) -> None

    """
    订阅合约行情。该操作会导致合约池内合约的增加，从而影响handle_bar中处理bar数据的数量。

    需要注意，用户在初次编写策略时候需要首先订阅合约行情，否则handle_bar不会被触发。

    :param id_or_symbols: 标的物

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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").are_valid_instruments())
def unsubscribe(id_or_symbols):
    # type: (Union[str, Instrument, Iterable[str], Iterable[Instrument]]) -> None

    """
    取消订阅合约行情。取消订阅会导致合约池内合约的减少，如果当前合约池中没有任何合约，则策略直接退出。

    :param id_or_symbols: 标的物

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
    EXECUTION_PHASE.OPEN_AUCTION,
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
    # type: (Optional[Union[str, date, datetime, pd.Timestamp]], str) -> pd.DataFrame
    """
    获取某个国家市场指定日期的收益率曲线水平。

    数据为2002年至今的中债国债收益率曲线，来源于中央国债登记结算有限责任公司。

    :param date: 查询日期，默认为策略当前日期前一天
    :param tenor: 标准期限，'0S' - 隔夜，'1M' - 1个月，'1Y' - 1年，默认为全部期限

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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(
    verify_that("order_book_id", pre_check=True).is_listed_instrument(),
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
    # type:(str, int, str, Optional[Union[str, List[str]]], Optional[bool], Optional[bool], Optional[str]) -> np.ndarray
    """
    获取指定合约的历史 k 线行情，同时支持日以及分钟历史数据。不能在init中调用。

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
    :param bar_count: 获取的历史数据数量，必填项
    :param frequency: 获取数据什么样的频率进行。'1d'、'1m' 和 '1w' 分别表示每日、每分钟和每周，必填项
    :param fields: 返回数据字段。必填项。见下方列表。
    :param skip_suspended: 是否跳过停牌数据
    :param include_now: 是否包含当前数据
    :param adjust_type: 复权类型，默认为前复权 pre；可选 pre, none, post

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

    if frequency[-1] not in {"m", "d", "w"}:
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
        ) or (ExecutionContext.phase() in (EXECUTION_PHASE.BEFORE_TRADING, EXECUTION_PHASE.OPEN_AUCTION)):
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
@apply_rules(
    verify_that("order_book_id", pre_check=True).is_listed_instrument(),
    verify_that('count').is_instance_of(int).is_greater_than(0)
)
def history_ticks(order_book_id, count):
    # type: (str, int) -> List[TickObject]
    """
    获取指定合约历史 tick 对象，仅支持在 tick 级别的策略（回测、模拟交易、实盘）中调用

    :param order_book_id: 合约代码
    :param count: 获取的 tick 数量

    """
    env = Environment.get_instance()
    sys_frequency = env.config.base.frequency
    if sys_frequency == "1d":
        raise RuntimeError("history_ticks does not support day bar backtest.")

    order_book_id = assure_order_book_id(order_book_id)
    dt = env.calendar_dt

    return env.data_proxy.history_ticks(order_book_id, count, dt)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
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
    # type: (str, Union[str, datetime, date]) -> pd.DataFrame
    """
    获取某个国家市场的所有合约信息。使用者可以通过这一方法很快地对合约信息有一个快速了解，目前仅支持中国市场。

    :param type: 需要查询合约类型，例如：type='CS'代表股票。默认是所有类型
    :param date: 查询时间点

    其中type参数传入的合约类型和对应的解释如下：

    =========================   ===================================================
    合约类型                      说明
    =========================   ===================================================
    CS                          Common Stock, 即股票
    ETF                         Exchange Traded Fund, 即交易所交易基金
    LOF                         Listed Open-Ended Fund，即上市型开放式基金
    INDX                        Index, 即指数
    Future                      Futures，即期货，包含股指、国债和商品期货
    =========================   ===================================================

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
                types.update(["ETF", "LOF"])
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
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbols").is_instance_of((str, Iterable)))
def instruments(id_or_symbols):
    # type: (Union[str, List[str]]) -> Union[Instrument, List[Instrument]]
    """
    获取某个国家市场内一个或多个合约的详细信息。目前仅支持中国市场。

    :param id_or_symbols: 合约代码或者合约代码列表

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
@apply_rules(
    verify_that("start_date").is_valid_date(ignore_none=False),
    verify_that("end_date").is_valid_date(ignore_none=False),
)
def get_trading_dates(start_date, end_date):
    # type: (Union[str, date, datetime, pd.Timestamp], Union[str, date, datetime, pd.Timestamp]) -> pd.DatetimeIndex
    """
    获取某个国家市场的交易日列表（起止日期加入判断）。目前仅支持中国市场。

    :param start_date: 开始日期
    :param end_date: 结束如期

    """
    return Environment.get_instance().data_proxy.get_trading_dates(start_date, end_date)


@export_as_api
@apply_rules(
    verify_that("date").is_valid_date(ignore_none=False),
    verify_that("n").is_instance_of(int).is_greater_or_equal_than(1),
)
def get_previous_trading_date(date, n=1):
    # type: (Union[str, date, datetime, pd.Timestamp], Optional[int]) -> date
    """
    获取指定日期的之前的第 n 个交易日。

    :param date: 指定日期
    :param n:

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_previous_trading_date(date='2016-05-02')
        [Out]
        [datetime.date(2016, 4, 29)]
    """
    return Environment.get_instance().data_proxy.get_previous_trading_date(date, n)


@export_as_api
@apply_rules(
    verify_that("date").is_valid_date(ignore_none=False),
    verify_that("n").is_instance_of(int).is_greater_or_equal_than(1),
)
def get_next_trading_date(date, n=1):
    # type: (Union[str, date, datetime, pd.Timestamp], Optional[int]) -> date
    """
    获取指定日期之后的第 n 个交易日

    :param date: 指定日期
    :param n:

    :example:

    ..  code-block:: python3
        :linenos:

        [In]get_next_trading_date(date='2016-05-01')
        [Out]
        [datetime.date(2016, 5, 3)]
    """
    return Environment.get_instance().data_proxy.get_next_trading_date(date, n)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("id_or_symbol").is_valid_instrument())
def current_snapshot(id_or_symbol):
    # type: (Union[str, Instrument]) -> Optional[TickObject]
    """
    获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。
    市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。
    在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。
    需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。
    如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

    :param d_or_symbol: 合约代码或简称

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
    # type: () -> List[Position]
    """
    获取所有持仓对象列表，

    :example:

    ..  code-block:: python3

        [In] get_positions()
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0}),
         BookingPosition({'order_book_id': '000010.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 0.0, 'avg_price': 3.09, 'last_price': 0, 'position_pnl': 0.0})]

    """
    portfolio = Environment.get_instance().portfolio
    return portfolio.get_positions()


@export_as_api
@apply_rules(
    verify_that("direction").is_in([POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT])
)
def get_position(order_book_id, direction=POSITION_DIRECTION.LONG):
    # type: (str, Optional[POSITION_DIRECTION]) -> Position
    """
    获取某个标的的持仓对象，

    :param order_book_id: 标的编号
    :param direction: 持仓方向

    :example:

    ..  code-block:: python3

        [In] get_position('000014.XSHE','long_positions")
        [Out]
        [BookingPosition({'order_book_id': '000014.XSHE', 'quantity': 100, 'direction': POSITION_DIRECTION.LONG, 'old_quantity': 0, 'trading_pnl': 1.0, 'avg_price': 9.56, 'last_price': 0, 'position_pnl': 0.0})]

    """
    portfolio = Environment.get_instance().portfolio
    return portfolio.get_position(order_book_id, direction)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT
)
@apply_rules(
    verify_that("event_type").is_instance_of(EVENT),
    verify_that("handler").is_instance_of(types.FunctionType),
)
def subscribe_event(event_type, handler):
    # type: (EVENT, Callable[[StrategyContext, Event], None]) -> None
    """
    订阅框架内部事件，注册事件处理函数

    :param event_type: 事件类型
    :param handler: 处理函数

    """
    env = Environment.get_instance()
    user_strategy = env.user_strategy
    env.event_bus.add_listener(
        event_type, user_strategy.wrap_user_event_handler(handler), user=True
    )


@export_as_api
def symbol(order_book_id, sep=", "):
    if isinstance(order_book_id, six.string_types):
        return "{}[{}]".format(order_book_id, Environment.get_instance().get_instrument(order_book_id).symbol)
    else:
        s = sep.join(symbol(item) for item in order_book_id)
        return s


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
def deposit(account_type, amount):
    # type: (str, float) -> None
    """
    入金（增加账户资金）

    :param account_type: 账户类型
    :param amount: 增加金额
    :return: None
    """
    env = Environment.get_instance()
    return env.portfolio.deposit_withdraw(account_type, amount)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that("account_type").is_in(DEFAULT_ACCOUNT_TYPE),
    verify_that("amount").is_number(),
)
def withdraw(account_type, amount):
    # type: (str, float) -> None
    """
    出金（减少账户资金）

    :param account_type: 账户类型
    :param amount: 减少金额
    :return: None
    """
    env = Environment.get_instance()
    return env.portfolio.deposit_withdraw(account_type, amount * -1)
