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
from rqalpha.const import SIDE, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


class StockPositionValidator(AbstractFrontendValidator):
    @staticmethod
    def _stock_validator(account, order):
        if order.side != SIDE.SELL:
            return True

        position = account.positions[order.order_book_id]
        if order.quantity <= position.sellable:
            return True

        user_system_log.warn(_(
            "Order Creation Failed: not enough stock {order_book_id} to sell, you want to sell {quantity},"
            " sellable {sellable}").format(
            order_book_id=order.order_book_id,
            quantity=order.quantity,
            sellable=position.sellable,
        ))
        return False

    def can_submit_order(self, account, order):
        if account.type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
            return self._stock_validator(account, order)
        return True

    def can_cancel_order(self, account, order):
        return True
