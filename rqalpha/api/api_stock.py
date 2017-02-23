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
from ..utils.logger import user_system_log
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
def order_shares(id_or_ins, amount, style=MarketOrder()):
    """
    落指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #购买Buy 2000 股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', 2000)
        #卖出2000股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', -2000)
        #购买1000股的平安银行股票，并以限价单发送，价格为￥10：
        order_shares('000001.XSHG', 1000, style=LimitOrder(10))
    """
    # Place an order by specified number of shares. Order type is also
    #     passed in as parameters if needed. If style is omitted, it fires a
    #     market order by default.
    # :PARAM id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float amount: Number of shares to order. Positive means buy,
    #     negative means sell. It will be rounded down to the closest
    #     integral multiple of the lot size
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
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
        user_system_log.warn(_("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
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
def order_lots(id_or_ins, amount, style=MarketOrder()):
    """
    指定手数发送买/卖单。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #买入20手的平安银行股票，并且发送市价单：
        order_lots('000001.XSHE', 20)
        #买入10手平安银行股票，并且发送限价单，价格为￥10：
        order_lots('000001.XSHE', 10, style=LimitOrder(10))

    """
    # Place an order by specified number of lots. Order type is also passed
    #     in as parameters if needed. If style is omitted, it fires a market
    #     order by default.
    # :param id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float amount: Number of lots to order. Positive means buy,
    #     negative means sell.
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
    order_book_id = assure_stock_order_book_id(id_or_ins)

    round_lot = int(ExecutionContext.get_instrument(order_book_id).round_lot)

    return order_shares(id_or_ins, amount * round_lot, style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder)))
def order_value(id_or_ins, cash_amount, style=MarketOrder()):
    """
    使用想要花费的金钱买入/卖出股票，而不是买入/卖出想要的股数，正数代表买入，负数代表卖出。股票的股数总是会被调整成对应的100的倍数（在A中国A股市场1手是100股）。当您提交一个卖单时，该方法代表的意义是您希望通过卖出该股票套现的金额。如果金额超出了您所持有股票的价值，那么您将卖出所有股票。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param float cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #买入价值￥10000的平安银行股票，并以市价单发送。如果现在平安银行股票的价格是￥7.5，那么下面的代码会买入1300股的平安银行，因为少于100股的数目将会被自动删除掉：
        order_value('000001.XSHE', 10000)
        #卖出价值￥10000的现在持有的平安银行：
        order_value('000001.XSHE', -10000)

    """
    # Place an order by specified value amount rather than specific number
    #     of shares/lots. Negative cash_amount results in selling the given
    #     amount of value, if the cash_amount is larger than you current
    #     security’s position, then it will sell all shares of this security.
    #     Orders are always truncated to whole lot shares.
    # :param id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float cash_amount: Cash amount to buy / sell the given value of
    #     securities. Positive means buy, negative means sell.
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
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
def order_percent(id_or_ins, percent, style=MarketOrder()):
    """
    发送一个等于目前投资组合价值（市场价值和目前现金的总和）一定百分比的买/卖单，正数代表买，负数代表卖。股票的股数总是会被调整成对应的一手的股票数的倍数（1手是100股）。百分比是一个小数，并且小于或等于1（<=100%），0.5表示的是50%.需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param float percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #买入等于现有投资组合50%价值的平安银行股票。如果现在平安银行的股价是￥10/股并且现在的投资组合总价值是￥2000，那么将会买入200股的平安银行股票。（不包含交易成本和滑点的损失）：
        order_percent('000001.XSHG', 0.5)
    """
    # Place an order for a security for a given percent of the current
    #     portfolio value, which is the sum of the positions value and
    #     ending cash balance. A negative percent order will result in
    #     selling given percent of current portfolio value. Orders are
    #     always truncated to whole shares. Percent should be a decimal
    #     number (0.50 means 50%), and its absolute value is <= 1.
    # :param id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float percent: Percent of the current portfolio value. Positive
    #     means buy, negative means selling give percent of the current
    #     portfolio value. Orders are always truncated according to lot size.
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
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
def order_target_value(id_or_ins, cash_amount, style=MarketOrder()):
    """
    买入/卖出并且自动调整该证券的仓位到一个目标价值。如果还没有任何该证券的仓位，那么会买入全部目标价值的证券。如果已经有了该证券的仓位，则会买入/卖出调整该证券的现在仓位和目标仓位的价值差值的数目的证券。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float cash_amount: 最终的该证券的仓位目标价值。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #如果现在的投资组合中持有价值￥3000的平安银行股票的仓位并且设置其目标价值为￥10000，以下代码范例会发送价值￥7000的平安银行的买单到市场。（向下调整到最接近每手股数即100的倍数的股数）：
        order_target_value('000001.XSHE', 10000)
    """
    # Place an order to adjust a position to a target value. If there is no
    #     position for the security, an order is placed for the whole amount
    #     of target value. If there is already a position for the security,
    #     an order is placed for the difference between target value and
    #     current position value.
    # :param id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float cash_amount: Target cash value for the adjusted position
    #     after placing order.
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
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
def order_target_percent(id_or_ins, percent, style=MarketOrder()):
    """
    买入/卖出证券以自动调整该证券的仓位到占有一个指定的投资组合的目标百分比。

    *   如果投资组合中没有任何该证券的仓位，那么会买入等于现在投资组合总价值的目标百分比的数目的证券。
    *   如果投资组合中已经拥有该证券的仓位，那么会买入/卖出目标百分比和现有百分比的差额数目的证券，最终调整该证券的仓位占据投资组合的比例至目标百分比。

    其实我们需要计算一个position_to_adjust (即应该调整的仓位)

    `position_to_adjust = target_position - current_position`

    投资组合价值等于所有已有仓位的价值和剩余现金的总和。买/卖单会被下舍入一手股数（A股是100的倍数）的倍数。目标百分比应该是一个小数，并且最大值应该<=1，比如0.5表示50%。

    如果position_to_adjust 计算之后是正的，那么会买入该证券，否则会卖出该证券。 需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float percent: 仓位最终所占投资组合总价值的目标百分比。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #如果投资组合中已经有了平安银行股票的仓位，并且占据目前投资组合的10%的价值，那么以下代码会买入平安银行股票最终使其占据投资组合价值的15%：
        order_target_percent('000001.XSHE', 0.15)
    """
    # Place an order to adjust position to a target percent of the portfolio
    #     value, so that your final position value takes the percentage you
    #     defined of your whole portfolio.
    #     position_to_adjust = target_position - current_position
    #     Portfolio value is calculated as sum of positions value and ending
    #     cash balance. The order quantity will be rounded down to integral
    #     multiple of lot size. Percent should be a decimal number (0.50
    #     means 50%), and its absolute value is <= 1. If the
    #     position_to_adjust calculated is positive, then it fires buy
    #     orders, otherwise it fires sell orders.
    # :param id_or_ins: the instrument to be ordered
    # :type id_or_ins: str or Instrument
    # :param float percent: Number of percent to order. It will be rounded down
    #     to the closest integral multiple of the lot size
    # :param style: Order type and default is `MarketOrder()`. The
    #     available order types are: `MarketOrder()` and
    #     `LimitOrder(limit_price)`
    # :return:  A unique order id.
    # :rtype: int
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
