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

from rqalpha.environment import Environment
from rqalpha.interface import AbstractBookingPosition
from rqalpha.const import POSITION_DIRECTION, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils.repr import property_repr
from rqalpha.utils import get_account_type
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _


class SimulationBookingPosition(AbstractBookingPosition):
    __repr__ = property_repr

    def __init__(self, position, direction):
        self._position = position
        self._direction = direction

    @property
    def order_book_id(self):
        return self._position.order_book_id

    @property
    def direction(self):
        return self._direction


class StockSimulationBookingPosition(SimulationBookingPosition):
    @property
    def quantity(self):
        if self._direction == POSITION_DIRECTION.SHORT:
            return 0
        return self._position.quantity

    @property
    def old_quantity(self):
        if self._direction == POSITION_DIRECTION.SHORT:
            return 0
        return self._position.sellable

    @property
    def today_quantity(self):
        return self.quantity - self.old_quantity

    @property
    def avg_price(self):
        if self._direction == POSITION_DIRECTION.SHORT:
            return 0
        return self._position.avg_price


class FutureSimulationBookingPosition(SimulationBookingPosition):
    @property
    def quantity(self):
        if self._direction == POSITION_DIRECTION.LONG:
            return self._position.buy_quantity
        else:
            return self._position.sell_quantity

    @property
    def old_quantity(self):
        if self._direction == POSITION_DIRECTION.LONG:
            return self._position.buy_old_quantity
        else:
            return self._position.sell_old_quantity

    @property
    def today_quantity(self):
        if self._direction == POSITION_DIRECTION.LONG:
            return self._position.buy_today_quantity
        else:
            return self._position.sell_today_quantity

    @property
    def avg_price(self):
        if self._direction == POSITION_DIRECTION.LONG:
            return self._position.buy_avg_open_price
        else:
            return self._position.sell_avg_open_price


class SimulationBooking(object):
    def __init__(self):
        self._env = Environment.get_instance()

    @property
    def _positions(self):
        portfolio = self._env.portfolio
        if not portfolio:
            raise RuntimeError(_('Cannot get portfolio instance.'))
        return portfolio.positions

    def get_positions(self):
        total_positions = []
        for order_book_id, position in six.iteritems(self._positions):
            for direction in [POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT]:
                booking_position = self.get_position(order_book_id, direction)
                if booking_position.quantity != 0:
                    total_positions.append(booking_position)

        return total_positions

    def get_position(self, order_book_id, direction):
        account_type = get_account_type(order_book_id)
        if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
            return StockSimulationBookingPosition(self._positions[order_book_id], direction)
        elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
            return FutureSimulationBookingPosition(self._positions[order_book_id], direction)
        else:
            raise NotImplementedError
