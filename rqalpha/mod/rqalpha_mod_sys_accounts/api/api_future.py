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
from typing import Union, Optional, List

from rqalpha.api import export_as_api
from rqalpha.apis.api_base import cal_style
from rqalpha.apis.api_rqdatac import futures
from rqalpha.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle
from rqalpha.const import (
    EXECUTION_PHASE, SIDE, POSITION_EFFECT, ORDER_TYPE, RUN_TYPE, INSTRUMENT_TYPE, POSITION_DIRECTION
)
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.base_position import BasePosition
from rqalpha.utils import is_valid_price
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.arg_checker import apply_rules, verify_that

__all__ = [
]


@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins', pre_check=True).is_valid_future(),
             verify_that('amount', pre_check=True).is_number().is_greater_or_equal_than(0),
             verify_that('side').is_in([SIDE.BUY, SIDE.SELL]),
             verify_that('position_effect').is_in([POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE]),
             verify_that('style', pre_check=True).is_instance_of((LimitOrder, MarketOrder, type(None))))
def order(id_or_ins, amount, side, position_effect, style):
    amount = int(amount)
    if amount == 0:
        user_system_log.warn(_(u"Order Creation Failed: Order amount is 0."))
        return None
    if isinstance(style, LimitOrder) and style.get_limit_price() <= 0:
        raise RQInvalidArgument(_(u"Limit order price should be positive"))

    instrument = assure_instrument(id_or_ins)
    order_book_id = instrument.order_book_id
    env = Environment.get_instance()
    if env.config.base.run_type != RUN_TYPE.BACKTEST and instrument.type == INSTRUMENT_TYPE.FUTURE:
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

    env = Environment.get_instance()

    orders = []

    if position_effect == POSITION_EFFECT.CLOSE:
        direction = POSITION_DIRECTION.LONG if side == SIDE.SELL else POSITION_DIRECTION.SHORT
        position = env.portfolio.get_position(order_book_id, direction)  # type: BasePosition
        quantity, old_quantity = position.quantity, position.old_quantity
        if amount > quantity:
            user_system_log.warn(_(
                u"Order Creation Failed: close amount {amount} is larger than position quantity {quantity}").format(
                amount=amount, quantity=quantity
            ))
            return []
        if amount > old_quantity:
            if old_quantity != 0:
                # 如果有昨仓，则创建一个 POSITION_EFFECT.CLOSE 的平仓单
                orders.append(Order.__from_create__(
                    order_book_id, old_quantity, side, style, POSITION_EFFECT.CLOSE
                ))
            # 剩下还有仓位，则创建一个 POSITION_EFFECT.CLOSE_TODAY 的平今单
            orders.append(Order.__from_create__(
                order_book_id, amount - old_quantity, side, style, POSITION_EFFECT.CLOSE_TODAY
            ))
        else:
            # 创建 POSITION_EFFECT.CLOSE 的平仓单
            orders.append(Order.__from_create__(order_book_id, amount, side, style, POSITION_EFFECT.CLOSE))
    elif position_effect == POSITION_EFFECT.OPEN:
        orders.append(Order.__from_create__(order_book_id, amount, side, style, position_effect))
    else:
        raise NotImplementedError()

    if len(orders) > 1:
        user_system_log.warn(_(
            "Order was separated, original order: {original_order_repr}, new orders: [{new_orders_repr}]").format(
                original_order_repr="Order(order_book_id={}, quantity={}, side={}, position_effect={})".format(
                    order_book_id, amount, side, position_effect
                ), new_orders_repr=", ".join(["Order({}, {}, {}, {})".format(
                    o.order_book_id, o.quantity, o.side, o.position_effect
                ) for o in orders])
            )
        )

    for o in orders:
        if o.type == ORDER_TYPE.MARKET:
            o.set_frozen_price(price)
        if env.can_submit_order(o):
            env.broker.submit_order(o)
        else:
            orders.remove(o)

    # 向前兼容，如果创建的order_list 只包含一个订单的话，直接返回对应的订单，否则返回列表
    if len(orders) == 1:
        return orders[0]
    else:
        return orders


@export_as_api
def buy_open(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Union[Order, List[Order], None]
    """
    买入开仓。

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #以价格为3500的限价单开仓买入2张上期所AG1607合约：
        buy_open('AG1607', amount=2, price=3500))
    """
    return order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def buy_close(id_or_ins, amount, price=None, style=None, close_today=False):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle], Optional[bool]) -> Union[Order, List[Order], None]
    """
    平卖仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :param close_today: 是否指定发平今仓单，默认为False，发送平仓单

    :example:

    .. code-block:: python

        #市价单将现有IF1603空仓买入平仓2张：
        buy_close('IF1603', 2)
    """
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return order(id_or_ins, amount, SIDE.BUY, position_effect, cal_style(price, style))


@export_as_api
def sell_open(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Union[Order, List[Order], None]
    """
    卖出开仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    """
    return order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def sell_close(id_or_ins, amount, price=None, style=None, close_today=False):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle], Optional[bool]) -> Union[Order, List[Order], None]
    """
    平买仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :param close_today: 是否指定发平今仓单，默认为False，发送平仓单
    """
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return order(id_or_ins, amount, SIDE.SELL, position_effect, cal_style(price, style))


@export_as_api
@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def get_future_contracts(underlying_symbol):
    # type: (str) -> List[str]
    """
    获取某一期货品种在策略当前日期的可交易合约order_book_id列表。按照到期月份，下标从小到大排列，返回列表中第一个合约对应的就是该品种的近月合约。

    :param underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'

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


futures.get_contracts = staticmethod(get_future_contracts)


def assure_instrument(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        return id_or_symbols
    else:
        return Environment.get_instance().data_proxy.instruments(id_or_symbols)

