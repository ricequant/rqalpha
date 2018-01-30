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

from __future__ import division
import six
import numpy as np

from rqalpha.api.api_base import decorate_api_exc, instruments, cal_style
from rqalpha.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle
from rqalpha.const import EXECUTION_PHASE, SIDE, POSITION_EFFECT, ORDER_TYPE, RUN_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils import is_valid_price
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.arg_checker import apply_rules, verify_that

__all__ = [
]


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED,
                                EXECUTION_PHASE.GLOBAL)
@apply_rules(verify_that('id_or_ins').is_valid_future(),
             verify_that('amount').is_number().is_greater_or_equal_than(0),
             verify_that('side').is_in([SIDE.BUY, SIDE.SELL]),
             verify_that('position_effect').is_in([POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE]),
             verify_that('style').is_instance_of((LimitOrder, MarketOrder, type(None))))
def order(id_or_ins, amount, side, position_effect, style):
    if not isinstance(style, OrderStyle):
        raise RuntimeError
    if amount < 0:
        raise RuntimeError
    if amount == 0:
        user_system_log.warn(_(u"Order Creation Failed: Order amount is 0."))
        return None
    if isinstance(style, LimitOrder) and style.get_limit_price() <= 0:
        raise RQInvalidArgument(_(u"Limit order price should be positive"))

    order_book_id = assure_future_order_book_id(id_or_ins)
    env = Environment.get_instance()
    if env.config.base.run_type != RUN_TYPE.BACKTEST:
        if "88" in order_book_id:
            raise RQInvalidArgument(_(u"Main Future contracts[88] are not supported in paper trading."))
        if "99" in order_book_id:
            raise RQInvalidArgument(_(u"Index Future contracts[99] are not supported in paper trading."))

    price = env.get_last_price(order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id)
        )
        return

    amount = int(amount)

    position = Environment.get_instance().portfolio.positions[order_book_id]

    orders = []
    if position_effect == POSITION_EFFECT.CLOSE:
        if side == SIDE.BUY:
            # 如果平仓量大于持仓量，则 Warning 并 取消订单创建
            if amount > position.sell_quantity:
                user_system_log.warn(
                    _(u"Order Creation Failed: close amount {amount} is larger than position "
                      u"quantity {quantity}").format(amount=amount, quantity=position.sell_quantity)
                )
                return []
            sell_old_quantity = position.sell_old_quantity
            if amount > sell_old_quantity:
                if sell_old_quantity != 0:
                    # 如果有昨仓，则创建一个 POSITION_EFFECT.CLOSE 的平仓单
                    orders.append(Order.__from_create__(
                        order_book_id,
                        sell_old_quantity,
                        side,
                        style,
                        POSITION_EFFECT.CLOSE
                    ))
                # 剩下还有仓位，则创建一个 POSITION_EFFECT.CLOSE_TODAY 的平今单
                orders.append(Order.__from_create__(
                    order_book_id,
                    amount - sell_old_quantity,
                    side,
                    style,
                    POSITION_EFFECT.CLOSE_TODAY
                ))
            else:
                # 创建 POSITION_EFFECT.CLOSE 的平仓单
                orders.append(Order.__from_create__(
                    order_book_id,
                    amount,
                    side,
                    style,
                    POSITION_EFFECT.CLOSE
                ))
        else:
            if amount > position.buy_quantity:
                user_system_log.warn(
                    _(u"Order Creation Failed: close amount {amount} is larger than position "
                      u"quantity {quantity}").format(amount=amount, quantity=position.buy_quantity)
                )
                return []
            buy_old_quantity = position.buy_old_quantity
            if amount > buy_old_quantity:
                if buy_old_quantity != 0:
                    orders.append(Order.__from_create__(
                        order_book_id,
                        buy_old_quantity,
                        side,
                        style,
                        POSITION_EFFECT.CLOSE
                    ))
                orders.append(Order.__from_create__(
                    order_book_id,
                    amount - buy_old_quantity,
                    side,
                    style,
                    POSITION_EFFECT.CLOSE_TODAY
                ))
            else:
                orders.append(Order.__from_create__(
                    order_book_id,
                    amount,
                    side,
                    style,
                    POSITION_EFFECT.CLOSE
                ))
    else:
        orders.append(Order.__from_create__(
            order_book_id,
            amount,
            side,
            style,
            position_effect
        ))

    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        for o in orders:
            o.mark_rejected(
                _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return orders

    for o in orders:
        if o.type == ORDER_TYPE.MARKET:
            o.set_frozen_price(price)
        if env.can_submit_order(o):
            env.broker.submit_order(o)

    # 向前兼容，如果创建的order_list 只包含一个订单的话，直接返回对应的订单，否则返回列表
    if len(orders) == 1:
        return orders[0]
    else:
        return orders


@export_as_api
def buy_open(id_or_ins, amount, price=None, style=None):
    """
    买入开仓。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #以价格为3500的限价单开仓买入2张上期所AG1607合约：
        buy_open('AG1607', amount=2, price=3500))
    """
    return order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def buy_close(id_or_ins, amount, price=None, style=None, close_today=False):
    """
    平卖仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :param bool close_today: 是否指定发平进仓单，默认为False，发送平仓单

    :return: :class:`~Order` object | list[:class:`~Order`]

    :example:

    .. code-block:: python

        #市价单将现有IF1603空仓买入平仓2张：
        buy_close('IF1603', 2)
    """
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return order(id_or_ins, amount, SIDE.BUY, position_effect, cal_style(price, style))


@export_as_api
def sell_open(id_or_ins, amount, price=None, style=None):
    """
    卖出开仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object
    """
    return order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def sell_close(id_or_ins, amount, price=None, style=None, close_today=False):
    """
    平买仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :param bool close_today: 是否指定发平进仓单，默认为False，发送平仓单

    :return: :class:`~Order` object | list[:class:`~Order`]
    """
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return order(id_or_ins, amount, SIDE.SELL, position_effect, cal_style(price, style))


def assure_future_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        if id_or_symbols.type != "Future":
            raise RQInvalidArgument(
                _(u"{order_book_id} is not supported in current strategy type").format(
                    order_book_id=id_or_symbols.order_book_id))
        else:
            return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_future_order_book_id(Environment.get_instance().data_proxy.instruments(id_or_symbols))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def get_future_contracts(underlying_symbol):
    """
    获取某一期货品种在策略当前日期的可交易合约order_book_id列表。按照到期月份，下标从小到大排列，返回列表中第一个合约对应的就是该品种的近月合约。

    :param str underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'

    :return: list[`str`]

    :example:

    获取某一天的主力合约代码（策略当前日期是20161201）:

        ..  code-block:: python

            [In]
            logger.info(get_future_contracts('IF'))
            [Out]
            ['IF1612', 'IF1701', 'IF1703', 'IF1706']
    """
    env = Environment.get_instance()
    return env.data_proxy.get_future_contracts(underlying_symbol, env.trading_dt)
