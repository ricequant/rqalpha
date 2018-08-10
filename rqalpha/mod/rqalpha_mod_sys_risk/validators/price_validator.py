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

from rqalpha.interface import AbstractFrontendValidator
from rqalpha.const import ORDER_TYPE
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


class PriceValidator(AbstractFrontendValidator):
    def __init__(self, env):
        self._env = env

    def can_submit_order(self, account, order):
        if order.type != ORDER_TYPE.LIMIT:
            return True

        limit_up = self._env.price_board.get_limit_up(order.order_book_id)
        if order.price > limit_up:
            reason = _(
                "Order Creation Failed: limit order price {limit_price} is higher than limit up {limit_up}."
            ).format(
                limit_price=order.price,
                limit_up=limit_up
            )
            user_system_log.warn(reason)
            return False

        limit_down = self._env.price_board.get_limit_down(order.order_book_id)
        if order.price < limit_down:
            reason = _(
                "Order Creation Failed: limit order price {limit_price} is lower than limit down {limit_down}."
            ).format(
                limit_price=order.price,
                limit_down=limit_down
            )
            user_system_log.warn(reason)
            return False

        return True

    def can_cancel_order(self, account, order):
        return True
