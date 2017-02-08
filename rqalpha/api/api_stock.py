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

from decimal import Decimal, getcontext

import six

from .api_base import decorate_api_exc, instruments
from ..const import ACCOUNT_TYPE
from ..const import EXECUTION_PHASE, SIDE, ORDER_TYPE
from ..environment import Environment
from ..execution_context import ExecutionContext
from ..model.instrument import Instrument
from ..model.order import Order, OrderStyle, MarketOrder, LimitOrder
from ..utils.arg_checker import apply_rules, verify_that
from ..utils.exception import patch_user_exc
from ..utils.i18n import gettext as _
from ..utils.logger import user_log
from ..utils.scheduler import market_close, market_open
from ..utils import scheduler

# 使用Decimal 解决浮点数运算精度问题
getcontext().prec = 10

__all__ = [
    'market_open',
    'market_close',
    'scheduler',
]


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_shares(id_or_ins, amount, style=MarketOrder()) -> int:
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
    if not isinstance(style, OrderStyle):
        raise patch_user_exc(ValueError(_('style should be OrderStyle')))
    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise patch_user_exc(ValueError(_("Limit order price should be positive")))

    order_book_id = assure_stock_order_book_id(id_or_ins)
    bar_dict = ExecutionContext.get_current_bar_dict()
    bar = bar_dict[order_book_id]
    price = bar.close
    calendar_dt = ExecutionContext.get_current_calendar_dt()
    trading_dt = ExecutionContext.get_current_trading_dt()

    if amount > 0:
        side = SIDE.BUY
    else:
        amount = abs(amount)
        side = SIDE.SELL

    round_lot = int(ExecutionContext.data_proxy.instruments(order_book_id).round_lot)

    try:
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
    except ValueError:
        amount = 0

    r_order = Order.__from_create__(calendar_dt, trading_dt, order_book_id, amount, side, style, None)

    if bar.isnan or price == 0:
        user_log.warn(_("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        r_order._mark_rejected(_("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return r_order

    if amount == 0:
        # 如果计算出来的下单量为0, 则不生成Order, 直接返回None
        # 因为很多策略会直接在handle_bar里面执行order_target_percent之类的函数，经常会出现下一个量为0的订单，如果这些订单都生成是没有意义的。
        r_order._mark_rejected(_("Order Creation Failed: 0 order quantity"))
        return r_order
    if r_order.type == ORDER_TYPE.MARKET:
        bar_dict = ExecutionContext.get_current_bar_dict()
        r_order._frozen_price = bar_dict[order_book_id].close
    ExecutionContext.broker.submit_order(r_order)

    return r_order


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_lots(id_or_ins, amount, style=MarketOrder()) -> int:
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
    order_book_id = assure_stock_order_book_id(id_or_ins)

    round_lot = int(ExecutionContext.get_instrument(order_book_id).round_lot)

    return order_shares(id_or_ins, amount * round_lot, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_value(id_or_ins, cash_amount, style=MarketOrder()) -> int:
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
    if not isinstance(style, OrderStyle):
        raise patch_user_exc(ValueError(_('style should be OrderStyle')))
    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise patch_user_exc(ValueError(_("Limit order price should be positive")))

    order_book_id = assure_stock_order_book_id(id_or_ins)

    bar_dict = ExecutionContext.get_current_bar_dict()
    bar = bar_dict[order_book_id]
    price = bar.close

    if bar.isnan or price == 0:
        return order_shares(order_book_id, 0, style)

    account = ExecutionContext.accounts[ACCOUNT_TYPE.STOCK]
    round_lot = int(ExecutionContext.get_instrument(order_book_id).round_lot)

    if cash_amount > 0:
        cash_amount = min(cash_amount, account.portfolio.cash)

    if isinstance(style, MarketOrder):
        amount = int(Decimal(cash_amount) / Decimal(price) / Decimal(round_lot)) * round_lot
    else:
        amount = int(Decimal(cash_amount) / Decimal(style.get_limit_price()) / Decimal(round_lot)) * round_lot

    # if the cash_amount is larger than you current security’s position,
    # then it will sell all shares of this security.

    position = account.portfolio.positions[order_book_id]
    amount = downsize_amount(amount, position)

    return order_shares(order_book_id, amount, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_than(-1).is_less_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_percent(id_or_ins, percent, style=MarketOrder()) -> int:
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
    if percent < -1 or percent > 1:
        raise patch_user_exc(ValueError(_('percent should between -1 and 1')))

    account = ExecutionContext.accounts[ACCOUNT_TYPE.STOCK]
    portfolio_value = account.portfolio.portfolio_value
    return order_value(id_or_ins, portfolio_value * percent, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_target_value(id_or_ins, cash_amount, style=MarketOrder()) -> int:
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
    order_book_id = assure_stock_order_book_id(id_or_ins)

    bar_dict = ExecutionContext.get_current_bar_dict()
    bar = bar_dict[order_book_id]
    price = 0 if bar.isnan else bar.close

    position = ExecutionContext.accounts[ACCOUNT_TYPE.STOCK].portfolio.positions[order_book_id]

    current_value = position._quantity * price

    return order_value(order_book_id, cash_amount - current_value, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_than(0).is_less_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_target_percent(id_or_ins, percent, style=MarketOrder()) -> int:
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
    if percent < 0 or percent > 1:
        raise patch_user_exc(ValueError(_('percent should between 0 and 1')))
    order_book_id = assure_stock_order_book_id(id_or_ins)

    bar_dict = ExecutionContext.get_current_bar_dict()
    bar = bar_dict[order_book_id]
    price = 0 if bar.isnan else bar.close

    portfolio = ExecutionContext.accounts[ACCOUNT_TYPE.STOCK].portfolio
    position = portfolio.positions[order_book_id]

    current_value = position._quantity * price

    return order_value(order_book_id, portfolio.portfolio_value * percent - current_value, style)


def assure_stock_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        order_book_id = id_or_symbols.order_book_id
        """
        这所以使用XSHG和XSHE来判断是否可交易是因为股票类型策略支持很多种交易类型，比如CS, ETF, LOF, FenjiMU, FenjiA, FenjiB,
        INDX等，但实际其中部分由不能交易，所以不能直接按照类型区分该合约是否可以交易。而直接通过判断其后缀可以比较好的区分是否可以进行交易
        """
        if "XSHG" in order_book_id or "XSHE" in order_book_id:
            return order_book_id
        else:
            raise patch_user_exc(
                ValueError(_("{order_book_id} is not supported in current strategy type").format(
                    order_book_id=order_book_id)))
    elif isinstance(id_or_symbols, six.string_types):
        return assure_stock_order_book_id(instruments(id_or_symbols))
    else:
        raise patch_user_exc(KeyError(_("unsupported order_book_id type")))


def downsize_amount(amount, position):
    config = Environment.get_instance().config
    if not config.validator.close_amount:
        return amount
    if amount > 0:
        return amount
    else:
        amount = abs(amount)
        if amount > position.sellable:
            return -position.sellable
        else:
            return -amount
