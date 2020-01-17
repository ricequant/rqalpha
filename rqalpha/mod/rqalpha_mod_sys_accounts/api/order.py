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

from typing import Union, List

from rqalpha.model.order import OrderStyle, Order
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION, SIDE, POSITION_EFFECT

from .api_stock import order_shares
from .api_future import order


def order_stock(order_book_id, quantity, style, target):
    # type: (str, Union[int, float], OrderStyle, bool) -> List[Order]
    position = Environment.get_instance().portfolio.get_position(order_book_id, POSITION_DIRECTION.LONG)
    if target:
        quantity = quantity - position.quantity
    return order_shares(order_book_id, quantity, style=style)


def order_future(order_book_id, quantity, style, target):
    # type: (str, Union[int, float], OrderStyle, bool) -> List[Order]
    portfolio = Environment.get_instance().portfolio
    long_position = portfolio.get_position(order_book_id, POSITION_DIRECTION.LONG)
    short_position = portfolio.get_position(order_book_id, POSITION_DIRECTION.SHORT)
    if target:
        # For order_to
        quantity -= (long_position.quantity - short_position.quantity)
    orders = []

    if quantity > 0:
        old_to_be_close, today_to_be_close = short_position.old_quantity, short_position.today_quantity
        side = SIDE.BUY
    else:
        old_to_be_close, today_to_be_close = long_position.old_quantity, long_position.today_quantity
        side = SIDE.SELL

    if old_to_be_close > 0:
        orders.append(order(order_book_id, min(quantity, old_to_be_close), side, POSITION_EFFECT.CLOSE, style))
        quantity -= old_to_be_close
    if quantity <= 0:
        return orders
    if today_to_be_close > 0:
        orders.append(order(
            order_book_id, min(quantity, today_to_be_close), side, POSITION_EFFECT.CLOSE_TODAY, style
        ))
        quantity -= today_to_be_close
    if quantity <= 0:
        return orders
    orders.append(order(order_book_id, quantity, side, POSITION_EFFECT.OPEN, style))
    return orders
