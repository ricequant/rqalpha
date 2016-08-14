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


from __future__ import division
from functools import partial, wraps
from collections import Iterable
import copy

import six

from .instruments import Instrument
from .logger import user_log
from .utils import ExecutionContext, get_last_date
from .utils.history import HybridDataFrame, missing_handler
from .i18n import gettext as _
from .scheduler import scheduler
from .const import EXECUTION_PHASE
from .analyser.order_style import MarketOrder, LimitOrder


__all__ = [
    'scheduler',
    'LimitOrder',
    'MarketOrder',
]


def export_as_api(func):
    __all__.append(func.__name__)
    return func


def check_is_trading(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        id_or_ins = args[0]

        order_book_id = assure_order_book_id(id_or_ins)

        bar_dict = ExecutionContext.get_current_bar_dict()
        if not bar_dict[order_book_id].is_trading:
            user_log.error(_("Order Rejected: {order_book_id} is not trading.").format(
                order_book_id=order_book_id,
            ))
            return -1

        return func(*args, **kwargs)

    return wrapper


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_shares(id_or_ins, amount, style=None):
    """
    Place an order by specified number of shares. Order type is also
        passed in as parameters if needed. If style is omitted, it fires a
        market order by default.
    :PARAM id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float amount: Number of shares to order. Positive means buy,
        negative means sell. It will be rounded down to the closest
        integral multiple of the lot size
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    order_book_id = assure_order_book_id(id_or_ins)

    if amount == 0:
        user_log.error(_("order_shares {order_book_id} amount is 0.").format(
            order_book_id=order_book_id,
        ))
        return

    round_lot = int(get_data_proxy().instrument(order_book_id).round_lot)
    amount = int(amount) // round_lot * round_lot

    bar_dict = ExecutionContext.get_current_bar_dict()
    order = get_simu_exchange().create_order(bar_dict, order_book_id, amount, style)

    return order.order_id


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_lots(id_or_ins, amount, style=None):
    """
    Place an order by specified number of lots. Order type is also passed
        in as parameters if needed. If style is omitted, it fires a market
        order by default.
    :param id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float amount: Number of lots to order. Positive means buy,
        negative means sell.
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    order_book_id = assure_order_book_id(id_or_ins)

    round_lot = int(get_data_proxy().instrument(order_book_id).round_lot)

    return order_shares(order_book_id, amount * round_lot, style)


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_value(id_or_ins, cash_amount, style=None):
    """
    Place an order by specified value amount rather than specific number
        of shares/lots. Negative cash_amount results in selling the given
        amount of value, if the cash_amount is larger than you current
        security’s position, then it will sell all shares of this security.
        Orders are always truncated to whole lot shares.
    :param id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float cash_amount: Cash amount to buy / sell the given value of
        securities. Positive means buy, negative means sell.
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    order_book_id = assure_order_book_id(id_or_ins)

    # TODO market order might be different
    bar_dict = ExecutionContext.get_current_bar_dict()
    price = bar_dict[order_book_id].close
    round_lot = int(get_data_proxy().instrument(order_book_id).round_lot)
    amount = ((cash_amount // price) // round_lot) * round_lot

    # if the cash_amount is larger than you current security’s position,
    # then it will sell all shares of this security.
    position = get_simu_exchange().account.portfolio.positions[order_book_id]
    if amount < 0:
        if abs(amount) > position.sellable:
            amount = -position.sellable

    return order_shares(order_book_id, amount, style)


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_percent(id_or_ins, percent, style=None):
    """
    Place an order for a security for a given percent of the current
        portfolio value, which is the sum of the positions value and
        ending cash balance. A negative percent order will result in
        selling given percent of current portfolio value. Orders are
        always truncated to whole shares. Percent should be a decimal
        number (0.50 means 50%), and its absolute value is <= 1.
    :param id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float percent: Percent of the current portfolio value. Positive
        means buy, negative means selling give percent of the current
        portfolio value. Orders are always truncated according to lot size.
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    assert 0 < percent <= 1

    portfolio_value = get_simu_exchange().account.portfolio.portfolio_value
    return order_value(id_or_ins, portfolio_value * percent, style)


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_target_value(id_or_ins, cash_amount, style=None):
    """
    Place an order to adjust a position to a target value. If there is no
        position for the security, an order is placed for the whole amount
        of target value. If there is already a position for the security,
        an order is placed for the difference between target value and
        current position value.
    :param id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float cash_amount: Target cash value for the adjusted position
        after placing order.
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    order_book_id = assure_order_book_id(id_or_ins)

    # TODO market order might be different
    bar_dict = ExecutionContext.get_current_bar_dict()
    price = bar_dict[order_book_id].close
    position = get_simu_exchange().account.portfolio.positions[order_book_id]

    current_value = position.quantity * price

    return order_value(order_book_id, cash_amount - current_value, style)


@check_is_trading
@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def order_target_percent(id_or_ins, percent, style=None):
    """
    Place an order to adjust position to a target percent of the portfolio
        value, so that your final position value takes the percentage you
        defined of your whole portfolio.
        position_to_adjust = target_position - current_position
        Portfolio value is calculated as sum of positions value and ending
        cash balance. The order quantity will be rounded down to integral
        multiple of lot size. Percent should be a decimal number (0.50
        means 50%), and its absolute value is <= 1. If the
        position_to_adjust calculated is positive, then it fires buy
        orders, otherwise it fires sell orders.
    :param id_or_ins: the instrument to be ordered
    :type id_or_ins: str or Instrument
    :param float percent: Number of percent to order. It will be rounded down
        to the closest integral multiple of the lot size
    :param style: Order type and default is `MarketOrder()`. The
        available order types are: `MarketOrder()` and
        `LimitOrder(limit_price)`
    :return:  A unique order id.
    :rtype: int
    """
    order_book_id = assure_order_book_id(id_or_ins)

    # TODO market order might be different
    bar_dict = ExecutionContext.get_current_bar_dict()
    price = bar_dict[order_book_id].close
    position = get_simu_exchange().account.portfolio.positions[order_book_id]

    current_value = position.quantity * price
    portfolio_value = get_simu_exchange().account.portfolio.portfolio_value

    return order_value(order_book_id, portfolio_value * percent - current_value, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def get_order(order_id):
    """
    Get a specified order by the unique order_id. The order object will be
        discarded at end of handle_bar.
    :param int order_id: order’s unique identifier returned by function
        like `order_shares`
    :return: an `Order` object.
    """
    return get_simu_exchange().get_order(order_id)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def get_open_orders():
    return copy.deepcopy(get_simu_exchange().open_orders)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def cancel_order(order_id):
    get_simu_exchange().cancel_order(order_id)


@export_as_api
def update_universe(id_or_symbols):
    """
    This method takes one or a list of id_or_symbol(s) as argument(s), to
        update the current subscription set of the instruments. It takes
        effect on the next bar event.
    :param id_or_symbols: one or a list of id_or_symbol(s).
    :type id_or_symbols: str or an iterable of strings
    """
    if isinstance(id_or_symbols, six.string_types):
        id_or_symbols = [id_or_symbols]
    elif isinstance(id_or_symbols, Instrument):
        id_or_symbols = [Instrument.order_book_id]
    elif isinstance(id_or_symbols, Iterable):
        id_or_symbols = [
            (item.order_book_id if isinstance(item, Instrument) else item)
            for item in id_or_symbols
        ]
    else:
        raise RuntimeError(_("unknown type"))

    executor = get_strategy_executor()
    executor.current_universe = set(id_or_symbols)


@export_as_api
def instruments(id_or_symbols):
    """
    Convert a string or a list of strings as order_book_id to instrument
        object(s).
    :param id_or_symbols: Passed in strings / iterable of strings are
        interpreted as order_book_ids. China market’s order_book_ids are
        like ‘000001.XSHE’ while US’s market’s order_book_ids are like
        ‘AAPL.US’
    :type id_or_symbols: str or iterable of strings
    :return: one / a list of instrument(s) object(s) - by the
        id_or_symbol(s) requested.
    """
    if isinstance(id_or_symbols, six.string_types):
        return get_data_proxy().instrument(id_or_symbols)

    return map(get_data_proxy().instrument, id_or_symbols)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def history(bar_count, frequency, field):
    executor = get_strategy_executor()
    data_proxy = get_data_proxy()

    results = {}

    dt = ExecutionContext.get_current_dt().date()
    if ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
        dt = get_last_date(ExecutionContext.get_trading_params().trading_calendar, dt)

    # This make history slow
    for order_book_id in list(executor.current_universe):
        hist = data_proxy.history(order_book_id, dt, bar_count, frequency, field)
        results[order_book_id] = hist

    handler = partial(missing_handler, bar_count=bar_count, frequency=frequency, field=field)
    return HybridDataFrame(results, missing_handler=handler)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def last(order_book_id, bar_count, frequency, field):
    executor = get_strategy_executor()
    data_proxy = get_data_proxy()

    dt = ExecutionContext.get_current_dt().date()
    if ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
        dt = get_last_date(ExecutionContext.get_trading_params().trading_calendar, dt)

    data = data_proxy.last(order_book_id, dt, bar_count, frequency, field)
    return data


@export_as_api
def is_st_stock(order_book_id):
    """
    instrument, = _get_instruments([order_book_id])
    return instrument.is_st
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.HANDLE_BAR,
                                EXECUTION_PHASE.SCHEDULED)
def plot(series_name, value):
    """
    Add a point to custom series.
    :param str series_name: the name of custom series
    :param float value: the value of the series in this time
    :return: None
    """


def get_simu_exchange():
    return ExecutionContext.get_exchange()


def get_strategy_context():
    return ExecutionContext.get_strategy_context()


def get_strategy_executor():
    return ExecutionContext.get_strategy_executor()


def get_current_dt():
    return ExecutionContext.get_current_dt()


def get_data_proxy():
    return ExecutionContext.get_strategy_executor().data_proxy


def assure_order_book_id(id_or_ins):
    if isinstance(id_or_ins, Instrument):
        order_book_id = id_or_ins.order_book_id
    elif isinstance(id_or_ins, six.string_types):
        order_book_id = id_or_ins
    else:
        raise NotImplementedError

    return order_book_id
