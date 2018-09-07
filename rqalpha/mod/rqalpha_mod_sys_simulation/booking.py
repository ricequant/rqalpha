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
from rqalpha.events import EVENT
from rqalpha.utils import get_account_type
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _


class SimulationBookingPosition(AbstractBookingPosition):
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
        user_system_log.warn(_("Quantity of stock has not been classfied "))
        return 0

    @property
    def today_quantity(self):
        if self._direction == POSITION_DIRECTION.SHORT:
            return 0
        return self.quantity

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
        self._cached_booking_positions = {}

        self._env.event_bus.add_listener(EVENT.POST_SETTLEMENT, self._post_settlement)

    def _post_settlement(self, _):
        for order_book_id in list(six.iterkeys(self._cached_booking_positions)):
            if order_book_id not in self._positions:
                del self._cached_booking_positions[order_book_id]

    @property
    def _positions(self):
        portfolio = self._env.portfolio
        if not portfolio:
            raise RuntimeError(_('Cannot get portfolio instance.'))
        return portfolio.positions

    def _get_booking_positions_dict(self, order_book_id):
        def make_booking_position(obid, dir):
            account_type = get_account_type(obid)
            if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
                return StockSimulationBookingPosition(self._positions[obid], dir)
            elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
                return FutureSimulationBookingPosition(self._positions[obid], dir)
            else:
                raise NotImplementedError

        return self._cached_booking_positions.setdefault(order_book_id, {
            POSITION_DIRECTION.LONG: make_booking_position(order_book_id, POSITION_DIRECTION.LONG),
            POSITION_DIRECTION.SHORT: make_booking_position(order_book_id, POSITION_DIRECTION.SHORT)
        })

    def get_positions(self):
        total_positions = []

        for order_book_id in six.iterkeys(self._positions):
            for booking_position in six.itervalues(self._get_booking_positions_dict(order_book_id)):
                if booking_position.quantity != 0:
                    total_positions.append(booking_position)

        return total_positions

    def get_position(self, order_book_id, direction):
        return self._get_booking_positions_dict(order_book_id)[direction]
