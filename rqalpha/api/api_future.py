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
import six

from .api_base import decorate_api_exc, instruments
from ..execution_context import ExecutionContext
from ..model.order import Order, MarketOrder, LimitOrder, OrderStyle
from ..const import EXECUTION_PHASE, SIDE, POSITION_EFFECT, ORDER_TYPE
from ..model.instrument import Instrument
from ..utils.exception import patch_user_exc
from ..utils.logger import user_system_log
from ..utils.i18n import gettext as _
from ..utils.arg_checker import apply_rules, verify_that


__all__ = [
]


def export_as_api(func):
    __all__.append(func.__name__)

    func = decorate_api_exc(func)

    return func


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('id_or_ins').is_valid_future(),
             verify_that('amount').is_greater_than(0),
             verify_that('side').is_in([SIDE.BUY, SIDE.SELL]),
             verify_that('position_effect').is_in([POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE]),
             verify_that('style').is_instance_of((LimitOrder, MarketOrder)))
def order(id_or_ins, amount, side, position_effect, style):
    if not isinstance(style, OrderStyle):
        raise RuntimeError
    if amount <= 0:
        raise RuntimeError
    if isinstance(style, LimitOrder) and style.get_limit_price() <= 0:
        raise patch_user_exc(ValueError(_("Limit order price should be positive")))

    order_book_id = assure_future_order_book_id(id_or_ins)
    bar_dict = ExecutionContext.get_current_bar_dict()
    bar = bar_dict[order_book_id]
    price = bar.close

    amount = int(amount)

    calendar_dt = ExecutionContext.get_current_calendar_dt()
    trading_dt = ExecutionContext.get_current_trading_dt()
    r_order = Order.__from_create__(calendar_dt, trading_dt, order_book_id, amount, side, style, position_effect)

    if bar.isnan or price == 0:
        user_system_log.warn(_("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        r_order._mark_rejected(_("Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return r_order

    if r_order.type == ORDER_TYPE.MARKET:
        bar_dict = ExecutionContext.get_current_bar_dict()
        r_order._frozen_price = bar_dict[order_book_id].close
    ExecutionContext.broker.submit_order(r_order)
    return r_order


@export_as_api
def buy_open(id_or_ins, amount, style=MarketOrder()):
    """
    买入开仓。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #以价格为3500的限价单开仓买入2张上期所AG1607合约：
        buy_open('AG1607', amount=2, style=LimitOrder(3500))
    """
    return order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.OPEN, style)


@export_as_api
def buy_close(id_or_ins, amount, style=MarketOrder()):
    """
    平卖仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #市价单将现有IF1603空仓买入平仓2张：
        buy_close('IF1603', 2)
    """
    return order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.CLOSE, style)


@export_as_api
def sell_open(id_or_ins, amount, style=MarketOrder()):
    """
    卖出开仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object
    """
    return order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.OPEN, style)


@export_as_api
def sell_close(id_or_ins, amount, style=MarketOrder()):
    """
    平买仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object
    """
    return order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.CLOSE, style)


def assure_future_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        if id_or_symbols.type != "Future":
            raise patch_user_exc(
                ValueError(_("{order_book_id} is not supported in current strategy type").format(
                    order_book_id=id_or_symbols.order_book_id)))
        else:
            return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_future_order_book_id(instruments(id_or_symbols))
    else:
        raise patch_user_exc(KeyError(_("unsupported order_book_id type")))


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
    dt = ExecutionContext.get_current_trading_dt()
    return ExecutionContext.data_proxy.get_future_contracts(underlying_symbol, dt)
