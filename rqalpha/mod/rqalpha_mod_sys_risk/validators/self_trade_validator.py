# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.


from rqalpha.interface import AbstractFrontendValidator
from rqalpha.const import ORDER_TYPE, SIDE
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log


class SelfTradeValidator(AbstractFrontendValidator):
    def __init__(self, env):
        self._env = env

    def can_submit_order(self, order, account=None):
        open_orders = [o for o in self._env.get_open_orders(order.order_book_id) if o.side != order.side]
        if len(open_orders) == 0:
            return True
        reason = _("Create order failed, there are active orders leading to the risk of self-trade: [{}...]")
        if order.type == ORDER_TYPE.MARKET:
            user_system_log.warn(reason.format(open_orders[0]))
            return False
        if order.side == SIDE.BUY:
            for open_order in open_orders:
                if order.price >= open_order.price:
                    user_system_log.warn(reason.format(open_order))
                    return False
        else:
            for open_order in open_orders:
                if order.price <= open_order.price:
                    user_system_log.warn(reason.format(open_order))
                    return False

    def can_cancel_order(self, order, account=None):
        return True
