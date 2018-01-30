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

from decimal import Decimal, getcontext

import six

from rqalpha.api.api_base import decorate_api_exc, instruments, cal_style, register_api
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, EXECUTION_PHASE, SIDE, ORDER_TYPE
from rqalpha.environment import Environment
from rqalpha.execution_context import ExecutionContext
from rqalpha.model.instrument import Instrument
from rqalpha.model.order import Order, OrderStyle, MarketOrder, LimitOrder
from rqalpha.utils import is_valid_price
from rqalpha.utils.arg_checker import apply_rules, verify_that
# noinspection PyUnresolvedReferences
from rqalpha.utils.exception import patch_user_exc, RQInvalidArgument
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
# noinspection PyUnresolvedReferences
from rqalpha.utils.scheduler import market_close, market_open
# noinspection PyUnresolvedReferences
from rqalpha.utils import scheduler

# 使用Decimal 解决浮点数运算精度问题
getcontext().prec = 10

__all__ = [
    'market_open',
    'market_close',
    'scheduler',
]


register_api("scheduler", scheduler)


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_shares(id_or_ins, amount, price=None, style=None):
    """
    落指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

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
    if amount == 0:
        # 如果下单量为0，则认为其并没有发单，则直接返回None
        return None
    style = cal_style(price, style)
    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise RQInvalidArgument(_(u"Limit order price should be positive"))
    order_book_id = assure_stock_order_book_id(id_or_ins)
    env = Environment.get_instance()

    price = env.get_last_price(order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return

    if amount > 0:
        side = SIDE.BUY
    else:
        amount = abs(amount)
        side = SIDE.SELL

    round_lot = int(env.get_instrument(order_book_id).round_lot)

    try:
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
    except ValueError:
        amount = 0

    r_order = Order.__from_create__(order_book_id, amount, side, style, None)

    if price == 0:
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        r_order.mark_rejected(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return r_order

    if amount == 0:
        # 如果计算出来的下单量为0, 则不生成Order, 直接返回None
        # 因为很多策略会直接在handle_bar里面执行order_target_percent之类的函数，经常会出现下一个量为0的订单，如果这些订单都生成是没有意义的。
        r_order.mark_rejected(_(u"Order Creation Failed: 0 order quantity"))
        return r_order
    if r_order.type == ORDER_TYPE.MARKET:
        r_order.set_frozen_price(price)
    if env.can_submit_order(r_order):
        env.broker.submit_order(r_order)

    return r_order


def _sell_all_stock(order_book_id, amount, style):
    env = Environment.get_instance()
    order = Order.__from_create__(order_book_id, amount, SIDE.SELL, style, None)
    if amount == 0:
        order.mark_rejected(_(u"Order Creation Failed: 0 order quantity"))
        return order

    if env.can_submit_order(order):
        env.broker.submit_order(order)
    return order


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_lots(id_or_ins, amount, price=None, style=None):
    """
    指定手数发送买/卖单。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

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
    order_book_id = assure_stock_order_book_id(id_or_ins)

    round_lot = int(Environment.get_instance().get_instrument(order_book_id).round_lot)

    style = cal_style(price, style)

    return order_shares(id_or_ins, amount * round_lot, style=style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_value(id_or_ins, cash_amount, price=None, style=None):
    """
    使用想要花费的金钱买入/卖出股票，而不是买入/卖出想要的股数，正数代表买入，负数代表卖出。股票的股数总是会被调整成对应的100的倍数（在A中国A股市场1手是100股）。当您提交一个卖单时，该方法代表的意义是您希望通过卖出该股票套现的金额。如果金额超出了您所持有股票的价值，那么您将卖出所有股票。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param float cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

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

    style = cal_style(price, style)

    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise RQInvalidArgument(_(u"Limit order price should be positive"))

    order_book_id = assure_stock_order_book_id(id_or_ins)
    env = Environment.get_instance()

    price = env.get_last_price(order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return

    if price == 0:
        return order_shares(order_book_id, 0, style)

    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    round_lot = int(env.get_instrument(order_book_id).round_lot)

    if cash_amount > 0:
        cash_amount = min(cash_amount, account.cash)

    if isinstance(style, MarketOrder):
        amount = int(Decimal(cash_amount) / Decimal(price) / Decimal(round_lot)) * round_lot
    else:
        amount = int(Decimal(cash_amount) / Decimal(style.get_limit_price()) / Decimal(round_lot)) * round_lot

    # if the cash_amount is larger than you current security’s position,
    # then it will sell all shares of this security.

    position = account.positions[order_book_id]
    amount = downsize_amount(amount, position)

    return order_shares(order_book_id, amount, style=style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_or_equal_than(-1).is_less_or_equal_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_percent(id_or_ins, percent, price=None, style=None):
    """
    发送一个等于目前投资组合价值（市场价值和目前现金的总和）一定百分比的买/卖单，正数代表买，负数代表卖。股票的股数总是会被调整成对应的一手的股票数的倍数（1手是100股）。百分比是一个小数，并且小于或等于1（<=100%），0.5表示的是50%.需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param float percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #买入等于现有投资组合50%价值的平安银行股票。如果现在平安银行的股价是￥10/股并且现在的投资组合总价值是￥2000，那么将会买入200股的平安银行股票。（不包含交易成本和滑点的损失）：
        order_percent('000001.XSHG', 0.5)
    """
    if percent < -1 or percent > 1:
        raise RQInvalidArgument(_(u"percent should between -1 and 1"))

    style = cal_style(price, style)
    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    return order_value(id_or_ins, account.total_value * percent, style=style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_target_value(id_or_ins, cash_amount, price=None, style=None):
    """
    买入/卖出并且自动调整该证券的仓位到一个目标价值。如果还没有任何该证券的仓位，那么会买入全部目标价值的证券。如果已经有了该证券的仓位，则会买入/卖出调整该证券的现在仓位和目标仓位的价值差值的数目的证券。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float cash_amount: 最终的该证券的仓位目标价值。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #如果现在的投资组合中持有价值￥3000的平安银行股票的仓位并且设置其目标价值为￥10000，以下代码范例会发送价值￥7000的平安银行的买单到市场。（向下调整到最接近每手股数即100的倍数的股数）：
        order_target_value('000001.XSHE', 10000)
    """
    order_book_id = assure_stock_order_book_id(id_or_ins)
    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    position = account.positions[order_book_id]

    style = cal_style(price, style)
    if cash_amount == 0:
        return _sell_all_stock(order_book_id, position.sellable, style)

    return order_value(order_book_id, cash_amount - position.market_value, style=style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_or_equal_than(0).is_less_or_equal_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_target_percent(id_or_ins, percent, price=None, style=None):
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

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #如果投资组合中已经有了平安银行股票的仓位，并且占据目前投资组合的10%的价值，那么以下代码会买入平安银行股票最终使其占据投资组合价值的15%：
        order_target_percent('000001.XSHE', 0.15)
    """
    if percent < 0 or percent > 1:
        raise RQInvalidArgument(_(u"percent should between 0 and 1"))
    order_book_id = assure_stock_order_book_id(id_or_ins)

    style = cal_style(price, style)

    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    position = account.positions[order_book_id]

    if percent == 0:
        return _sell_all_stock(order_book_id, position.sellable, style)

    return order_value(order_book_id, account.total_value * percent - position.market_value, style=style)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('count').is_greater_than(0))
def is_suspended(order_book_id, count=1):
    """
    判断某只股票是否全天停牌。

    :param str order_book_id: 某只股票的代码或股票代码，可传入单只股票的order_book_id, symbol

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :return: count为1时 `bool`; count>1时 `pandas.DataFrame`
    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_stock_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_suspended(order_book_id, dt, count)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument())
def is_st_stock(order_book_id, count=1):
    """
    判断股票在一段时间内是否为ST股（包括ST与*ST）。

    ST股是有退市风险因此风险比较大的股票，很多时候您也会希望判断自己使用的股票是否是'ST'股来避开这些风险大的股票。另外，我们目前的策略比赛也禁止了使用'ST'股。

    :param str order_book_id: 某只股票的代码，可传入单只股票的order_book_id, symbol

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :return: count为1时 `bool`; count>1时 `pandas.DataFrame`
    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_stock_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_st_stock(order_book_id, dt, count)


def assure_stock_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_stock_order_book_id(instruments(id_or_symbols))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))


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
