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

import six
from decimal import Decimal

from rqalpha.api.api_base import instruments, cal_style
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION, POSITION_EFFECT, SIDE
from rqalpha.model.instrument import Instrument
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.model.order import Order, MarketOrder, LimitOrder
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.logger import user_system_log
from rqalpha import export_as_api
from rqalpha.utils.i18n import gettext as _

from . import mod_name


@export_as_api
def get_positions(booking=None):
    env = Environment.get_instance()
    mod = env.mod_dict[mod_name]
    booking_account = mod.booking_account
    return booking_account.get_positions(booking)


@export_as_api
@apply_rules(verify_that('direction').is_in([POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT]))
def get_position(order_book_id, direction, booking=None):
    env = Environment.get_instance()
    mod = env.mod_dict[mod_name]
    booking_account = mod.booking_account
    return booking_account.get_position(order_book_id, direction, booking)


@export_as_api
@apply_rules(
    verify_that('id_or_ins').is_valid_future(),
    verify_that('amount').is_number().is_greater_or_equal_than(0),
    verify_that('side').is_in([SIDE.BUY, SIDE.SELL]),
    verify_that('position_effect').is_in([POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY]),
    verify_that('style').is_instance_of((LimitOrder, MarketOrder, type(None))))
def send_order(order_book_id, amount, side, position_effect, style):
    env = Environment.get_instance()

    order = Order.__from_create__(order_book_id, amount, side, style, position_effect)
    env.broker.submit_order(order)
    return order


@export_as_api
def buy_open(id_or_ins, amount, price=None, style=None):
    return send_order(id_or_ins, amount, SIDE.BUY, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def sell_close(id_or_ins, amount, price=None, style=None, close_today=False):
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return send_order(id_or_ins, amount, SIDE.SELL, position_effect, cal_style(price, style))


@export_as_api
def sell_open(id_or_ins, amount, price=None, style=None):
    return send_order(id_or_ins, amount, SIDE.SELL, POSITION_EFFECT.OPEN, cal_style(price, style))


@export_as_api
def buy_close(id_or_ins, amount, price=None, style=None, close_today=False):
    position_effect = POSITION_EFFECT.CLOSE_TODAY if close_today else POSITION_EFFECT.CLOSE
    return send_order(id_or_ins, amount, SIDE.BUY, position_effect, cal_style(price, style))


@export_as_api
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_shares(id_or_ins, amount, price=None, style=None):
    order_book_id = assure_order_book_id(id_or_ins)
    env = Environment.get_instance()

    if amount > 0:
        side = SIDE.BUY
        position_effect = POSITION_EFFECT.OPEN
    else:
        amount = abs(amount)
        side = SIDE.SELL
        position_effect = POSITION_EFFECT.CLOSE

    round_lot = int(env.get_instrument(order_book_id).round_lot)
    try:
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
    except ValueError:
        amount = 0

    order = Order.__from_create__(order_book_id, amount, side, style, position_effect)

    if amount == 0:
        # 如果计算出来的下单量为0, 则不生成Order, 直接返回None
        # 因为很多策略会直接在handle_bar里面执行order_target_percent之类的函数，经常会出现下一个量为0的订单，如果这些订单都生成是没有意义的。
        user_system_log.warn(_(u"Order Creation Failed: 0 order quantity"))
        return

    env.broker.submit_order(order)
    return order


def assure_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_order_book_id(instruments(id_or_symbols))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))