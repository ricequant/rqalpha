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
from rqalpha.apis.api_base import assure_instrument
from rqalpha.apis.api_abstract import order, order_to, buy_open, buy_close, sell_open, sell_close
from rqalpha.apis.api_base import cal_style
from rqalpha.apis.api_rqdatac import futures
from rqalpha.environment import Environment
from rqalpha.model.order import Order, LimitOrder, OrderStyle
from rqalpha.const import SIDE, POSITION_EFFECT, ORDER_TYPE, RUN_TYPE, INSTRUMENT_TYPE, POSITION_DIRECTION
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.position import Position
from rqalpha.utils import is_valid_price
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.arg_checker import apply_rules, verify_that


__all__ = [
]


def _submit_order(id_or_ins, amount, side, position_effect, style):
    instrument = assure_instrument(id_or_ins)
    order_book_id = instrument.order_book_id
    env = Environment.get_instance()

    amount = int(amount)
    if amount == 0:
        user_system_log.warn(_(
            u"Order Creation Failed: 0 order quantity, order_book_id={order_book_id}"
        ).format(order_book_id=order_book_id))
        return None
    if isinstance(style, LimitOrder) and style.get_limit_price() <= 0:
        raise RQInvalidArgument(_(u"Limit order price should be positive"))


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
    if position_effect in (POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.CLOSE):
        direction = POSITION_DIRECTION.LONG if side == SIDE.SELL else POSITION_DIRECTION.SHORT
        position = env.portfolio.get_position(order_book_id, direction)  # type: Position
        if position_effect == POSITION_EFFECT.CLOSE_TODAY:
            if amount > position.today_closable:
                user_system_log.warning(_(
                    "Order Creation Failed: "
                    "close today amount {amount} is larger than today closable quantity {quantity}"
                ).format(amount=amount, quantity=position.today_closable))
                return []
            orders.append(Order.__from_create__(
                order_book_id, amount, side, style, POSITION_EFFECT.CLOSE_TODAY
            ))
        else:
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


def _order(order_book_id, quantity, style, target):
    # type: (str, Union[int, float], OrderStyle, bool) -> List[Order]
    portfolio = Environment.get_instance().portfolio
    long_position = portfolio.get_position(order_book_id, POSITION_DIRECTION.LONG)
    short_position = portfolio.get_position(order_book_id, POSITION_DIRECTION.SHORT)
    if target:
        # For order_to
        quantity -= (long_position.quantity - short_position.quantity)
    orders = []

    if quantity > 0:
        # 平空头，开多头
        position_to_be_closed = short_position
        side = SIDE.BUY
    else:
        # 平多头，开空头
        position_to_be_closed = long_position
        side = SIDE.SELL
        quantity *= -1

    old_to_be_closed, today_to_be_closed = position_to_be_closed.old_quantity, position_to_be_closed.today_quantity
    if old_to_be_closed > 0:
        # 平昨仓
        orders.append(_submit_order(order_book_id, min(quantity, old_to_be_closed), side, POSITION_EFFECT.CLOSE, style))
        quantity -= old_to_be_closed
    if quantity <= 0:
        return orders
    if today_to_be_closed > 0:
        # 平今仓
        orders.append(_submit_order(
            order_book_id, min(quantity, today_to_be_closed), side, POSITION_EFFECT.CLOSE_TODAY, style
        ))
        quantity -= today_to_be_closed
    if quantity <= 0:
        return orders
    # 开仓
    orders.append(_submit_order(order_book_id, quantity, side, POSITION_EFFECT.OPEN, style))
    return orders


@order.register(INSTRUMENT_TYPE.FUTURE)
def future_order(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    return _order(order_book_id, quantity, cal_style(price, style), False)


@order_to.register(INSTRUMENT_TYPE.FUTURE)
def future_order_to(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    return _order(order_book_id, quantity, cal_style(price, style), True)


@buy_open.register(INSTRUMENT_TYPE.FUTURE)
def future_buy_open(id_or_ins, amount, price=None, style=None):
    return _submit_order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.OPEN, cal_style(price, style))


@buy_close.register(INSTRUMENT_TYPE.FUTURE)
def future_buy_close(id_or_ins, amount, price=None, style=None, close_today=False):
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return _submit_order(id_or_ins, amount, SIDE.BUY, position_effect, cal_style(price, style))


@sell_open.register(INSTRUMENT_TYPE.FUTURE)
def future_sell_open(id_or_ins, amount, price=None, style=None):
    return _submit_order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.OPEN, cal_style(price, style))


@sell_close.register(INSTRUMENT_TYPE.FUTURE)
def future_sell_close(id_or_ins, amount, price=None, style=None, close_today=False):
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return _submit_order(id_or_ins, amount, SIDE.SELL, position_effect, cal_style(price, style))


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
