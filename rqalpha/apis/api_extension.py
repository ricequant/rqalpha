# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import six
from typing import Union, Optional, List

from rqalpha.api import export_as_api
from rqalpha.apis.api_base import cal_style
from rqalpha.environment import Environment
from rqalpha.utils.arg_checker import apply_rules, verify_that

# noinspection PyUnresolvedReferences
from rqalpha.model.order import LimitOrder, MarketOrder, Order, OrderStyle
from rqalpha.model.instrument import Instrument


@export_as_api
def symbol(order_book_id, sep=", "):
    if isinstance(order_book_id, six.string_types):
        return "{}[{}]".format(order_book_id, Environment.get_instance().get_instrument(order_book_id).symbol)
    else:
        s = sep.join(symbol(item) for item in order_book_id)
        return s


@export_as_api
@apply_rules(verify_that("quantity").is_number())
def order(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    """
    全品种通用智能调仓函数

    如果不指定 price, 则相当于下 MarketOrder

    如果 order_book_id 是股票，等同于调用 order_shares

    如果 order_book_id 是期货，则进行智能下单:

        *   quantity 表示调仓量
        *   如果 quantity 为正数，则先平 Sell 方向仓位，再开 Buy 方向仓位
        *   如果 quantity 为负数，则先平 Buy 反向仓位，再开 Sell 方向仓位

    :param order_book_id: 下单标的物
    :param quantity: 调仓量
    :param price: 下单价格
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    ..  code-block:: python3
        :linenos:

        # 当前仓位为0
        # RB1710 多方向调仓2手：调整后变为 BUY 2手
        order('RB1710', 2)

        # RB1710 空方向调仓3手：先平多方向2手 在开空方向1手，调整后变为 SELL 1手
        order('RB1710', -3)

    """
    style = cal_style(price, style)
    orders = Environment.get_instance().portfolio.order(order_book_id, quantity, style)

    if isinstance(orders, Order):
        return [orders]
    return orders


@export_as_api
@apply_rules(verify_that("quantity").is_number())
def order_to(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    """
    全品种通用智能调仓函数

    如果不指定 price, 则相当于 MarketOrder

    如果 order_book_id 是股票，则表示仓位调整到多少股

    如果 order_book_id 是期货，则进行智能调仓:

        *   quantity 表示调整至某个仓位
        *   quantity 如果为正数，则先平 SELL 方向仓位，再 BUY 方向开仓 quantity 手
        *   quantity 如果为负数，则先平 BUY 方向仓位，再 SELL 方向开仓 -quantity 手

    :param order_book_id: 下单标的物
    :param int quantity: 调仓量
    :param float price: 下单价格
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :example:

    ..  code-block:: python3
        :linenos:

        # 当前仓位为0
        # RB1710 调仓至 BUY 2手
        order_to('RB1710', 2)

        # RB1710 调仓至 SELL 1手
        order_to('RB1710', -1)

    """
    style = cal_style(price, style)
    orders = Environment.get_instance().portfolio.order(
        order_book_id, quantity, style, target=True
    )

    if isinstance(orders, Order):
        return [orders]
    return orders
