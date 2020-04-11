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

import math
import datetime
from itertools import chain
from dateutil.parser import parse
from decimal import Decimal, getcontext
from typing import Dict, List, Union, Optional

import six
import pandas as pd
import numpy as np

from rqalpha.api import export_as_api
from rqalpha.apis.api_base import instruments, cal_style
from rqalpha.const import (
    DEFAULT_ACCOUNT_TYPE, EXECUTION_PHASE, SIDE, ORDER_TYPE, POSITION_EFFECT, FRONT_VALIDATOR_TYPE, POSITION_DIRECTION,
    INSTRUMENT_TYPE
)
from rqalpha.environment import Environment
from rqalpha.execution_context import ExecutionContext
from rqalpha.model.instrument import (
    Instrument, IndustryCode as industry_code, IndustryCodeItem, SectorCode as sector_code, SectorCodeItem
)
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle
from rqalpha.interface import AbstractPosition
from rqalpha.utils import is_valid_price
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
from rqalpha.mod.rqalpha_mod_sys_scheduler.scheduler import market_close, market_open
from rqalpha.mod.rqalpha_mod_sys_scheduler import scheduler

# 使用Decimal 解决浮点数运算精度问题
getcontext().prec = 10

export_as_api(market_close)
export_as_api(market_open)
export_as_api(industry_code, name='industry_code')
export_as_api(sector_code, name='sector_code')


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_shares(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :param amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

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
        user_system_log.warn(_(u"Order Creation Failed: Order amount is 0."))
        return None
    style = cal_style(price, style)
    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise RQInvalidArgument(_(u"Limit order price should be positive"))
    order_book_id = assure_stock_order_book_id(id_or_ins)
    auto_switch_order_value = Environment.get_instance().config.mod.sys_accounts.auto_switch_order_value
    return _order_shares(order_book_id, amount, style, auto_switch_order_value)


def _order_shares(order_book_id, amount, style, auto_switch_order_value):
    env = Environment.get_instance()

    price = env.get_last_price(order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return

    if amount > 0:
        side = SIDE.BUY
        position_effect = POSITION_EFFECT.OPEN
    else:
        amount = abs(amount)
        side = SIDE.SELL
        position_effect = POSITION_EFFECT.CLOSE

    if side == SIDE.BUY:
        # 卖出不再限制 round_lot, order_shares 不再依赖 portfolio
        round_lot = int(env.get_instrument(order_book_id).round_lot)
        try:
            amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
        except ValueError:
            amount = 0

    r_order = Order.__from_create__(order_book_id, amount, side, style, position_effect)

    if amount == 0:
        # 如果计算出来的下单量为0, 则不生成Order, 直接返回None
        # 因为很多策略会直接在handle_bar里面执行order_target_percent之类的函数，经常会出现下一个量为0的订单，如果这些订单都生成是没有意义的。
        user_system_log.warn(_(u"Order Creation Failed: 0 order quantity"))
        return
    if r_order.type == ORDER_TYPE.MARKET:
        r_order.set_frozen_price(price)

    reject_validator_type = env.validate_order_submission(r_order)
    if not reject_validator_type:
        env.broker.submit_order(r_order)
        return r_order
    else:
        if auto_switch_order_value and reject_validator_type == FRONT_VALIDATOR_TYPE.CASH:
            remaining_cash = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name].cash
            user_system_log.warn(_(
                "Insufficient cash, use all remaining cash({}) to create order").format(remaining_cash)
            )
            return _order_value(order_book_id, remaining_cash, style)


def _sell_all_stock(order_book_id, amount, style):
    env = Environment.get_instance()
    order = Order.__from_create__(order_book_id, amount, SIDE.SELL, style, POSITION_EFFECT.CLOSE)
    if amount == 0:
        user_system_log.warn(_(u"Order Creation Failed: 0 order quantity"))
        return

    if env.can_submit_order(order):
        env.broker.submit_order(order)
        return order


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_lots(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    指定手数发送买/卖单。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

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
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_value(id_or_ins, cash_amount, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    使用想要花费的金钱买入/卖出股票，而不是买入/卖出想要的股数，正数代表买入，负数代表卖出。股票的股数总是会被调整成对应的100的倍数（在A中国A股市场1手是100股）。如果资金不足，该API将不会创建发送订单。

    需要注意：
    当您提交一个买单时，cash_amount 代表的含义是您希望买入股票消耗的金额（包含税费），最终买入的股数不仅和发单的价格有关，还和税费相关的参数设置有关。
    当您提交一个卖单时，cash_amount 代表的意义是您希望卖出股票的总价值。如果金额超出了您所持有股票的价值，那么您将卖出所有股票。

    :param id_or_ins: 下单标的物
    :param cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #花费最多￥10000买入平安银行股票，并以市价单发送。具体下单的数量与您策略税费相关的配置有关。
        order_value('000001.XSHE', 10000)
        #卖出价值￥10000的现在持有的平安银行：
        order_value('000001.XSHE', -10000)

    """

    style = cal_style(price, style)

    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise RQInvalidArgument(_(u"Limit order price should be positive"))

    order_book_id = assure_stock_order_book_id(id_or_ins)
    return _order_value(order_book_id, cash_amount, style)


def _order_value(order_book_id, cash_amount, style):
    env = Environment.get_instance()

    price = env.get_last_price(order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return

    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]

    if cash_amount > 0:
        cash_amount = min(cash_amount, account.cash)

    price = price if isinstance(style, MarketOrder) else style.get_limit_price()
    amount = int(Decimal(cash_amount) / Decimal(price))

    if cash_amount > 0:
        round_lot = int(env.get_instrument(order_book_id).round_lot)

        # FIXME: logic duplicate with order_shares
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot

        while amount > 0:
            dummy_order = Order.__from_create__(order_book_id, amount, SIDE.BUY, LimitOrder(price),
                                                POSITION_EFFECT.OPEN)
            expected_transaction_cost = env.get_order_transaction_cost(dummy_order)
            if amount * price + expected_transaction_cost <= cash_amount:
                break
            amount -= round_lot
        else:
            user_system_log.warn(_(u"Order Creation Failed: 0 order quantity"))
            return

    # if the cash_amount is larger than you current security’s position,
    # then it will sell all shares of this security.

    position = account.get_position(order_book_id, POSITION_DIRECTION.LONG)
    amount = downsize_amount(amount, position)

    return _order_shares(order_book_id, amount, style, auto_switch_order_value=False)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_or_equal_than(-1).is_less_or_equal_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_percent(id_or_ins, percent, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    发送一个花费价值等于目前投资组合（市场价值和目前现金的总和）一定百分比现金的买/卖单，正数代表买，负数代表卖。股票的股数总是会被调整成对应的一手的股票数的倍数（1手是100股）。百分比是一个小数，并且小于或等于1（<=100%），0.5表示的是50%.需要注意，如果资金不足，该API将不会创建发送订单。

    需要注意：
    发送买单时，percent 代表的是期望买入股票消耗的金额（包含税费）占投资组合总权益的比例。
    发送卖单时，percent 代表的是期望卖出的股票总价值占投资组合总权益的比例。

    :param id_or_ins: 下单标的物
    :param percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #花费等于现有投资组合50%价值的现金买入平安银行股票：
        order_percent('000001.XSHG', 0.5)
    """
    if percent < -1 or percent > 1:
        raise RQInvalidArgument(_(u"percent should between -1 and 1"))

    style = cal_style(price, style)
    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    return order_value(id_or_ins, account.total_value * percent, style=style)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('cash_amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_target_value(id_or_ins, cash_amount, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    买入/卖出并且自动调整该证券的仓位到一个目标价值。
    加仓时，cash_amount 代表现有持仓的价值加上即将花费（包含税费）的现金的总价值。
    减仓时，cash_amount 代表调整仓位的目标价至。

    需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :param cash_amount: 最终的该证券的仓位目标价值。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #如果现在的投资组合中持有价值￥3000的平安银行股票的仓位，以下代码范例会发送花费 ￥7000 现金的平安银行买单到市场。（向下调整到最接近每手股数即100的倍数的股数）：
        order_target_value('000001.XSHE', 10000)
    """
    order_book_id = assure_stock_order_book_id(id_or_ins)
    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
    position = account.get_position(order_book_id, POSITION_DIRECTION.LONG)  # type: AbstractPosition

    style = cal_style(price, style)
    if cash_amount == 0:
        return _sell_all_stock(order_book_id, position.closable, style)

    try:
        market_value = position.market_value
    except RuntimeError:
        order_result = order_value(order_book_id, np.nan, style=style)
        if order_result:
            raise
    else:
        return order_value(order_book_id, cash_amount - market_value, style=style)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('percent').is_number().is_greater_or_equal_than(0).is_less_or_equal_than(1),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_target_percent(id_or_ins, percent, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    买入/卖出证券以自动调整该证券的仓位到占有一个目标价值。

    加仓时，percent 代表证券已有持仓的价值加上即将花费的现金（包含税费）的总值占当前投资组合总价值的比例。
    减仓时，percent 代表证券将被调整到的目标价至占当前投资组合总价值的比例。

    其实我们需要计算一个position_to_adjust (即应该调整的仓位)

    `position_to_adjust = target_position - current_position`

    投资组合价值等于所有已有仓位的价值和剩余现金的总和。买/卖单会被下舍入一手股数（A股是100的倍数）的倍数。目标百分比应该是一个小数，并且最大值应该<=1，比如0.5表示50%。

    如果position_to_adjust 计算之后是正的，那么会买入该证券，否则会卖出该证券。 需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :param percent: 仓位最终所占投资组合总价值的目标百分比。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #如果投资组合中已经有了平安银行股票的仓位，并且占据目前投资组合的10%的价值，那么以下代码会消耗相当于当前投资组合价值5%的现金买入平安银行股票：
        order_target_percent('000001.XSHE', 0.15)
    """
    if percent < 0 or percent > 1:
        raise RQInvalidArgument(_(u"percent should between 0 and 1"))
    order_book_id = assure_stock_order_book_id(id_or_ins)

    style = cal_style(price, style)

    account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    position = account.get_position(order_book_id, POSITION_DIRECTION.LONG)  # type: AbstractPosition

    if percent == 0:
        return _sell_all_stock(order_book_id, position.closable, style)

    try:
        market_value = position.market_value
    except RuntimeError:
        order_result = order_value(order_book_id, np.nan, style=style)
        if order_result:
            raise
    else:
        return order_value(order_book_id, account.total_value * percent - market_value, style=style)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
def order_target_portfolio(target_portfolio):
    # type: (Dict[Union[str, Instrument]: float]) -> List[Order]
    """
    买入/卖出证券以批量调整证券的仓位，以期使其持仓市值占账户总权益的比重达到指定值。

    :param target_portfolio: 下单标的物及其目标市值占比的字典

    :example:

    .. code-block:: python

        # 调整仓位，以使平安银行和万科 A 的持仓占比分别达到 10% 和 15%
        order_target_portfolio({
            '000001.XSHE': 0.1
            '000002.XSHE': 0.15
        })
    """

    if isinstance(target_portfolio, pd.Series):
        # FIXME: kind of dirty
        total_percent = sum(target_portfolio)
    else:
        total_percent = sum(six.itervalues(target_portfolio))
    if total_percent > 1:
        raise RQInvalidArgument(_(u"total percent should be lower than 1, current: {}").format(total_percent))

    env = Environment.get_instance()
    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    account_value = account.total_value
    target_quantities = {}
    for id_or_ins, target_percent in six.iteritems(target_portfolio):
        order_book_id = assure_stock_order_book_id(id_or_ins)
        if target_percent < 0:
            raise RQInvalidArgument(_(u"target percent of {} should between 0 and 1, current: {}").format(
                order_book_id, target_percent
            ))
        price = env.data_proxy.get_last_price(order_book_id)
        if not is_valid_price(price):
            user_system_log.warn(
                _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id)
            )
            continue
        target_quantities[order_book_id] = account_value * target_percent / price

    close_orders, open_orders = [], []
    current_quantities = {
        p.order_book_id: p.quantity for p in account.get_positions() if p.direction == POSITION_DIRECTION.LONG
    }
    for order_book_id, quantity in six.iteritems(current_quantities):
        if order_book_id not in target_portfolio:
            close_orders.append(Order.__from_create__(
                order_book_id, quantity, SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    round_lot = 100
    for order_book_id, target_quantity in six.iteritems(target_quantities):
        if order_book_id in current_quantities:
            delta_quantity = target_quantity - current_quantities[order_book_id]
        else:
            delta_quantity = target_quantity

        if delta_quantity >= round_lot:
            delta_quantity = math.floor(delta_quantity / round_lot) * round_lot
            open_orders.append(Order.__from_create__(
                order_book_id, delta_quantity, SIDE.BUY, MarketOrder(), POSITION_EFFECT.OPEN
            ))
        elif delta_quantity < -1:
            delta_quantity = math.floor(delta_quantity)
            close_orders.append(Order.__from_create__(
                order_book_id, abs(delta_quantity), SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    submit_orders = []
    for order in chain(close_orders, open_orders):
        if env.can_submit_order(order):
            submit_orders.append(order)
            env.broker.submit_order(order)
    return submit_orders


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.OPEN_AUCTION,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('count').is_greater_than(0))
def is_suspended(order_book_id, count=1):
    # type: (str, Optional[int]) -> Union[bool, pd.DataFrame]
    """
    判断某只股票是否全天停牌。

    :param order_book_id: 某只股票的代码或股票代码，可传入单只股票的order_book_id, symbol
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_stock_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_suspended(order_book_id, dt, count)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.OPEN_AUCTION,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument())
def is_st_stock(order_book_id, count=1):
    # type: (str, Optional[int]) -> Union[bool, pd.DataFrame]
    """
    判断股票在一段时间内是否为ST股（包括ST与*ST）。

    ST股是有退市风险因此风险比较大的股票，很多时候您也会希望判断自己使用的股票是否是'ST'股来避开这些风险大的股票。另外，我们目前的策略比赛也禁止了使用'ST'股。

    :param order_book_id: 某只股票的代码，可传入单只股票的order_book_id, symbol
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_stock_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_st_stock(order_book_id, dt, count)


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
@apply_rules(verify_that("code").is_instance_of((str, IndustryCodeItem)))
def industry(code):
    # type: (str) -> List[str]
    """
    获得属于某一行业的所有股票列表。

    :param code: 行业名称或行业代码。例如，农业可填写industry_code.A01 或 'A01'

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
    if isinstance(code, IndustryCodeItem):
        code = code.code
    else:
        code = to_industry_code(code)
    cs_instruments = Environment.get_instance().data_proxy.all_instruments((INSTRUMENT_TYPE.CS, ))
    return [i.order_book_id for i in cs_instruments if i.industry_code == code]


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
@apply_rules(verify_that("code").is_instance_of((str, SectorCodeItem)))
def sector(code):
    # type: (str) -> List[str]
    """
    获得属于某一板块的所有股票列表。

    :param code: 板块名称或板块代码。例如，能源板块可填写'Energy'、'能源'或sector_code.Energy

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
    if isinstance(code, SectorCodeItem):
        code = code.name
    else:
        code = to_sector_name(code)

    cs_instruments = Environment.get_instance().data_proxy.all_instruments((INSTRUMENT_TYPE.CS,))
    return [i.order_book_id for i in cs_instruments if i.sector_code == code]


@export_as_api
@apply_rules(
    verify_that("order_book_id").is_valid_instrument(),
    verify_that("start_date").is_valid_date(ignore_none=False),
)
def get_dividend(order_book_id, start_date):
    # type: (str, Union[str, datetime.date, datetime.datetime, pd.Timestamp]) -> Optional[np.ndarray]
    """
    获取某只股票到策略当前日期前一天的分红情况（包含起止日期）。

    :param order_book_id: 股票代码
    :param start_date: 开始日期，需要早于策略当前日期

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

    :example:

    获取平安银行2013-01-04 到策略当前日期前一天的分红数据:

    ..  code-block:: python3
        :linenos:

        get_dividend('000001.XSHE', start_date='20130104')
        #[Out]
        #array([(20130614, 20130619, 20130620, 20130620,  1.7 , 10),
        #       (20140606, 20140611, 20140612, 20140612,  1.6 , 10),
        #       (20150407, 20150410, 20150413, 20150413,  1.74, 10),
        #       (20160608, 20160615, 20160616, 20160616,  1.53, 10)],
        #      dtype=[('announcement_date', '<u4'), ('book_closure_date', '<u4'), ('ex_dividend_date', '<u4'), ('payable_date', '<u4'), ('dividend_cash_before_tax', '<f8'), ('round_lot', '<u4')])

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
    order_book_id = assure_stock_order_book_id(order_book_id)
    array = env.data_proxy.get_dividend(order_book_id)
    if array is None:
        return None

    sd = start_date.year * 10000 + start_date.month * 100 + start_date.day
    ed = dt.year * 10000 + dt.month * 100 + dt.day
    return array[
        (array["announcement_date"] >= sd) & (array["announcement_date"] <= ed)
    ]


def to_industry_code(s):
    for __, v in six.iteritems(industry_code.__dict__):
        if isinstance(v, IndustryCodeItem):
            if v.name == s:
                return v.code
    return s


def to_sector_name(s):
    for __, v in six.iteritems(sector_code.__dict__):
        if isinstance(v, SectorCodeItem):
            if v.cn == s or v.en == s or v.name == s:
                return v.name
    # not found
    return s


def to_date(date):
    if isinstance(date, six.string_types):
        return parse(date).date()

    if isinstance(date, datetime.datetime):
        try:
            return date.date()
        except AttributeError:
            return date

    raise RQInvalidArgument("unknown date value: {}".format(date))


def assure_stock_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_stock_order_book_id(instruments(id_or_symbols))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))


def downsize_amount(amount, position):
    # type: (float, AbstractPosition) -> float
    config = Environment.get_instance().config
    if not config.validator.close_amount:
        return amount
    if amount > 0:
        return amount
    else:
        amount = abs(amount)
        if amount > position.closable:
            return -position.closable
        else:
            return -amount
