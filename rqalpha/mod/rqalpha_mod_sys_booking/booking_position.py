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
from rqalpha.const import SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils.logger import user_system_log, system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import property_repr


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


class BookingPosition(object):

    __repr__ = property_repr

    def __init__(self, order_book_id, direction):
        self._order_book_id = order_book_id
        self._direction = direction

        self._old_quantity = 0
        self._today_quantity = 0

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

    def apply_settlement(self):
        self._old_quantity += self._today_quantity
        self._today_quantity = 0

    def apply_trade(self, trade):
        position_effect = self._get_position_effect(trade.side, trade.position_effect)

        if position_effect == POSITION_EFFECT.OPEN:
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
