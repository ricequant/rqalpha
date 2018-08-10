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
from rqalpha.const import SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


class FuturePositionValidator(AbstractFrontendValidator):
    @staticmethod
    def _future_validator(account, order):
        if order.position_effect == POSITION_EFFECT.OPEN:
            return True

        position = account.positions[order.order_book_id]

        if order.side == SIDE.BUY and order.position_effect == POSITION_EFFECT.CLOSE_TODAY \
                and order.quantity > position._closable_today_sell_quantity:
            user_system_log.warn(_(
                "Order Creation Failed: not enough today position {order_book_id} to buy close, target"
                " quantity is {quantity}, closable today quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position._closable_today_sell_quantity,
            ))
            return False

        if order.side == SIDE.SELL and order.position_effect == POSITION_EFFECT.CLOSE_TODAY \
                and order.quantity > position._closable_today_buy_quantity:
            user_system_log.warn(_(
                "Order Creation Failed: not enough today position {order_book_id} to sell close, target"
                " quantity is {quantity}, closable today quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position._closable_today_buy_quantity,
            ))
            return False

        if order.side == SIDE.BUY and order.quantity > position.closable_sell_quantity:
            user_system_log.warn(_(
                "Order Creation Failed: not enough securities {order_book_id} to buy close, target"
                " sell quantity is {quantity}, sell_closable_quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position.closable_sell_quantity,
            ))
            return False

        elif order.side == SIDE.SELL and order.quantity > position.closable_buy_quantity:
            user_system_log.warn(_(
                "Order Creation Failed: not enough securities {order_book_id} to sell close, target"
                " sell quantity is {quantity}, buy_closable_quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position.closable_buy_quantity,
            ))
            return False
        return True

    def can_submit_order(self, account, order):
        if account.type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
            return self._future_validator(account, order)
        return True

    def can_cancel_order(self, account, order):
        return True
