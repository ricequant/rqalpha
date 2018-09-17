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

from rqalpha.environment import Environment
from rqalpha.interface import AbstractBookingPosition
from rqalpha.const import POSITION_DIRECTION, POSITION_EFFECT, SIDE
from rqalpha.events import EVENT
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import property_repr


class Booking(object):
    def __init__(self, long_positions, short_positions, backward_trade_set=None):
        self._positions_dict = {
            POSITION_DIRECTION.LONG: long_positions,
            POSITION_DIRECTION.SHORT: short_positions,
        }
        self._backward_trade_set = backward_trade_set or set()
        self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.prepend_listener(EVENT.POST_SETTLEMENT, lambda e: self._apply_settlement())
        event_bus.add_listener(EVENT.TRADE, lambda e: self.apply_trade(e.trade))

    def order(self, order_book_id, quantity, style, target=False):
        # TODO: Strategy may have only a booking instance instead of portfolio
        pass

    def get_position(self, order_book_id, direction):
        return self._positions_dict[direction].get_or_create(order_book_id)

    def get_positions(self):
        total_positions = []
        for direction, positions in self._positions_dict.items():
            for order_book_id, position in positions.items():
                if position.quantity != 0:
                    total_positions.append(position)
        return total_positions

    def _apply_settlement(self, check_delist=True):
        delete_list = []

        for direction, positions in self._positions_dict.items():
            for order_book_id, position in positions.items():
                if check_delist and position.is_de_listed() and position.quantity != 0:
                    user_system_log.warn(
                        _(u"{order_book_id} is expired, close all positions by system").format(
                            order_book_id=order_book_id))
                    delete_list.append((order_book_id, direction))
                    # del self._positions[order_book_id]
                elif position.quantity == 0:
                    delete_list.append((order_book_id, direction))
                    # del self._positions[order_book_id]
                else:
                    position.apply_settlement()

        for order_book_id, direction in delete_list:
            self._positions_dict[direction].pop(order_book_id)

        self._backward_trade_set.clear()

    def apply_trade(self, trade):
        if trade.exec_id in self._backward_trade_set:
            return

        order_book_id = trade.order_book_id

        long_positions = self._positions_dict[POSITION_DIRECTION.LONG]
        short_positions = self._positions_dict[POSITION_DIRECTION.SHORT]

        if trade.position_effect == POSITION_EFFECT.OPEN:
            if trade.side == SIDE.BUY:
                position = long_positions.get_or_create(order_book_id)
            elif trade.side == SIDE.SELL:
                position = short_positions.get_or_create(order_book_id)
            else:
                raise RuntimeError("unknown side, trade {}".format(trade))
        elif trade.position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY):
            if trade.side == SIDE.BUY:
                position = short_positions.get_or_create(order_book_id)
            elif trade.side == SIDE.SELL:
                position = long_positions.get_or_create(order_book_id)
            else:
                raise RuntimeError("unknown side, trade {}".format(trade))
        else:
            # NOTE: 股票如果没有position_effect就特殊处理
            position = long_positions.get_or_create(order_book_id)

        position.apply_trade(trade)
        self._backward_trade_set.add(trade.exec_id)


class BookingPositions(dict):
    def __init__(self, direction):
        super(BookingPositions, self).__init__()
        self.direction = direction
        self._cached_positions = {}

    def __missing__(self, key):
        if key not in self._cached_positions:
            self._cached_positions[key] = BookingPosition(key, self.direction)
        return self._cached_positions[key]

    def get_or_create(self, key):
        if key not in self:
            self[key] = BookingPosition(key, self.direction)
        return self[key]


class BookingPosition(AbstractBookingPosition):
    __repr__ = property_repr

    def __init__(self, order_book_id, direction):
        self._order_book_id = order_book_id
        self._direction = direction

        self._old_quantity = 0
        self._today_quantity = 0

        self._avg_price = 0

    @property
    def order_book_id(self):
        """
        [Required]

        返回当前持仓的 order_book_id
        """
        return self._order_book_id

    @property
    def direction(self):
        """
        [Required]

        持仓方向
        """
        return self._direction

    @property
    def quantity(self):
        """
        [float] 总仓位
        """
        return self.old_quantity + self.today_quantity

    @property
    def old_quantity(self):
        """
        [float] 昨仓
        """
        return self._old_quantity

    @property
    def today_quantity(self):
        """
        [float] 今仓
        """
        return self._today_quantity

    @property
    def avg_price(self):
        """
        [float] 平均开仓价格
        """
        return self._avg_price

    def apply_settlement(self):
        self._old_quantity += self._today_quantity
        self._today_quantity = 0

    def apply_trade(self, trade):
        position_effect = self._get_position_effect(trade.side, trade.position_effect)

        if position_effect == POSITION_EFFECT.OPEN:
            if self.quantity < 0:
                if trade.last_quantity <= -1 * self.quantity:
                    self._avg_price = 0
                else:
                    self._avg_price = trade.last_price
            else:
                self._avg_price = (
                        self.quantity * self.avg_price + trade.last_quantity * trade.last_price
                ) / (self.quantity + trade.last_quantity)
            self._today_quantity += trade.last_quantity
        elif position_effect == POSITION_EFFECT.CLOSE_TODAY:
            self._today_quantity -= trade.last_quantity
        elif position_effect == POSITION_EFFECT.CLOSE:
            # 先平昨，后平今
            self._old_quantity -= trade.last_quantity
            if self._old_quantity < 0:
                self._today_quantity += self._old_quantity
                self._old_quantity = 0

    def is_de_listed(self):
        """
        判断合约是否过期
        """
        # FIXME: 股票期货分开判断
        instrument = Environment.get_instance().get_instrument(self.order_book_id)
        current_date = Environment.get_instance().trading_dt
        if instrument.de_listed_date is not None and current_date >= instrument.de_listed_date:
            return True
        return False

    @staticmethod
    def _get_position_effect(side, position_effect):
        if position_effect is None:
            # NOTE: 股票如果没有position_effect就特殊处理
            if side == SIDE.BUY:
                return POSITION_EFFECT.OPEN
            elif side == SIDE.SELL:
                return POSITION_EFFECT.CLOSE
        return position_effect
