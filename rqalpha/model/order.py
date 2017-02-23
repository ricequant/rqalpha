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
import time

from ..const import ORDER_STATUS, SIDE, POSITION_EFFECT, ORDER_TYPE
from ..utils import id_gen
from ..utils.repr import property_repr, properties
from ..utils.logger import user_system_log


OrderPersistMap = {
    "_order_id": "_order_id",
    "_calendar_dt": "_calendar_dt",
    "_trading_dt": "_trading_dt",
    "_quantity": "_quantity",
    "_order_book_id": "_order_book_id",
    "_side": "_side",
    "_position_effect": "_position_effect",
    "_message": "_message",
    "_filled_quantity": "_filled_quantity",
    "_status": "_status",
    "_frozen_price": "_frozen_price",
    "_type": "_type",
    "_avg_price": "_avg_price",
    "_transaction_cost": "_transaction_cost",
}


class Order(object):

    order_id_gen = id_gen(int(time.time()))

    __repr__ = property_repr

    def __init__(self):
        self._order_id = None
        self._calendar_dt = None
        self._trading_dt = None
        self._quantity = None
        self._order_book_id = None
        self._side = None
        self._position_effect = None
        self._message = None
        self._filled_quantity = None
        self._status = None
        self._frozen_price = None
        self._type = None
        self._avg_price = None
        self._transaction_cost = None

    @classmethod
    def __from_create__(cls, calendar_dt, trading_dt, order_book_id, quantity, side, style, position_effect):
        order = cls()
        order._order_id = next(order.order_id_gen)
        order._calendar_dt = calendar_dt
        order._trading_dt = trading_dt
        order._quantity = quantity
        order._order_book_id = order_book_id
        order._side = side
        order._position_effect = position_effect
        order._message = ""
        order._filled_quantity = 0
        order._status = ORDER_STATUS.PENDING_NEW
        if isinstance(style, LimitOrder):
            order._frozen_price = style.get_limit_price()
            order._type = ORDER_TYPE.LIMIT
        else:
            order._frozen_price = 0.
            order._type = ORDER_TYPE.MARKET
        order._avg_price = 0
        order._transaction_cost = 0
        return order

    @classmethod
    def __from_dict__(cls, order_dict):
        order = cls()
        for persist_key, origin_key in six.iteritems(OrderPersistMap):
            setattr(order, origin_key, order_dict[persist_key])
        return order

    def __to_dict__(self):
        order_dict = {}
        for persist_key, origin_key in six.iteritems(OrderPersistMap):
            order_dict[persist_key] = getattr(self, origin_key)
        return order_dict

    @property
    def order_id(self):
        """
        【int】唯一标识订单的id
        """
        return self._order_id

    @property
    def trading_datetime(self):
        """
        【datetime.datetime】订单的交易日期（对应期货夜盘）
        """
        return self._trading_dt

    @property
    def datetime(self):
        """
        【datetime.datetime】订单创建时间
        """
        return self._calendar_dt

    @property
    def quantity(self):
        """
        【int】订单数量
        """
        return self._quantity

    @property
    def unfilled_quantity(self):
        """
        【int】订单未成交数量
        """
        return self._quantity - self._filled_quantity

    @property
    def order_book_id(self):
        """
        【str】合约代码
        """
        return self._order_book_id

    @property
    def side(self):
        """
        【SIDE】订单方向
        """
        return self._side

    @property
    def position_effect(self):
        """
        【POSITION_EFFECT】订单开平（期货专用）
        """
        return self._position_effect

    @property
    def message(self):
        """
        【str】信息。比如拒单时候此处会提示拒单原因
        """
        return self._message

    @property
    def filled_quantity(self):
        """
        【int】订单已成交数量
        """
        return self._filled_quantity

    @property
    def status(self):
        """
        【ORDER_STATUS】订单状态
        """
        return self._status

    @property
    def price(self):
        """
        【float】订单价格，只有在订单类型为'限价单'的时候才有意义
        """
        return 0 if self.type == ORDER_TYPE.MARKET else self._frozen_price

    @property
    def type(self):
        """
        【ORDER_TYPE】订单类型
        """
        return self._type

    @property
    def avg_price(self):
        """
        【float】成交均价
        """
        return self._avg_price

    @property
    def transaction_cost(self):
        """
        【float】费用
        """
        return self._transaction_cost

    def _is_final(self):
        if self.status == ORDER_STATUS.PENDING_NEW or self.status == ORDER_STATUS.ACTIVE:
            return False
        else:
            return True

    def _is_active(self):
        return self.status == ORDER_STATUS.ACTIVE

    def _active(self):
        self._status = ORDER_STATUS.ACTIVE

    def _fill(self, trade):
        amount = trade.last_quantity
        assert self.filled_quantity + amount <= self.quantity
        new_quantity = self._filled_quantity + amount
        self._avg_price = (self._avg_price * self._filled_quantity + trade.last_price * amount) / new_quantity
        self._transaction_cost += trade.commission + trade.tax
        self._filled_quantity = new_quantity
        if self.unfilled_quantity == 0:
            self._status = ORDER_STATUS.FILLED

    def _mark_rejected(self, reject_reason):
        if not self._is_final():
            self._message = reject_reason
            self._status = ORDER_STATUS.REJECTED
            user_system_log.warn(reject_reason)

    def _mark_cancelled(self, cancelled_reason, user_warn=True):
        if not self._is_final():
            self._message = cancelled_reason
            self._status = ORDER_STATUS.CANCELLED
            if user_warn:
                user_system_log.warn(cancelled_reason)

    def __simple_object__(self):
        return properties(self)


class OrderStyle:
    def get_limit_price(self):
        raise NotImplementedError


class MarketOrder(OrderStyle):
    __repr__ = ORDER_TYPE.MARKET.__repr__

    def get_limit_price(self):
        return None


class LimitOrder(OrderStyle):
    __repr__ = ORDER_TYPE.LIMIT.__repr__

    def __init__(self, limit_price):
        self.limit_price = float(limit_price)

    def get_limit_price(self):
        return self.limit_price
