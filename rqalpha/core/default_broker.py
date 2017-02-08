# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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

import jsonpickle

from .default_matcher import DefaultMatcher
from ..trader.account import init_accounts
from ..interface import AbstractBroker, Persistable
from ..utils import get_account_type
from ..utils.i18n import gettext as _
from ..events import Events
from ..const import MATCHING_TYPE, ORDER_STATUS, ACCOUNT_TYPE
from ..trader.frontend_validator import StockFrontendValidator, FutureFrontendValidator


class DefaultBroker(AbstractBroker, Persistable):
    def __init__(self, env):
        self._env = env
        if env.config.base.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE:
            self._matcher = DefaultMatcher(lambda bar: bar.close, env.config.validator.bar_limit)
            self._match_immediately = True
        else:
            self._matcher = DefaultMatcher(lambda bar: bar.open, env.config.validator.bar_limit)
            self._match_immediately = False

        self._accounts = None
        self._open_orders = []
        self._board = None
        self._turnover = {}
        self._delayed_orders = []
        self._frontend_validator = {}

    def get_accounts(self):
        if self._accounts is None:
            self._accounts = init_accounts(self._env.config)
        return self._accounts

    def get_open_orders(self):
        return self._open_orders

    def get_state(self):
        return jsonpickle.dumps([o.order_id for _, o in self._delayed_orders]).encode('utf-8')

    def set_state(self, state):
        delayed_orders = jsonpickle.loads(state.decode('utf-8'))
        for account in self._accounts.values():
            for o in account.daily_orders.values():
                if not o._is_final():
                    if o.order_id in delayed_orders:
                        self._delayed_orders.append((account, o))
                    else:
                        self._open_orders.append((account, o))

    def _get_account_for(self, order_book_id):
        account_type = get_account_type(order_book_id)
        return self._accounts[account_type]

    def _get_frontend_validator_for(self, order_book_id):
        account_type = get_account_type(order_book_id)
        try:
            return self._frontend_validator[account_type]
        except KeyError:
            if account_type == ACCOUNT_TYPE.STOCK:
                validator = StockFrontendValidator(self._env.config)
            elif account_type == ACCOUNT_TYPE.FUTURE:
                validator = FutureFrontendValidator(self._env.config)
            else:
                raise RuntimeError('account type {} not supported yet'.format(account_type))
            self._frontend_validator[account_type] = validator
            return validator

    def submit_order(self, order):
        account = self._get_account_for(order.order_book_id)
        frontend_validator = self._get_frontend_validator_for(order.order_book_id)
        validate_result = frontend_validator.order_pipeline(account, order)
        account.append_order(order)
        if not validate_result:
            return

        account.on_order_creating(order)
        if self._env.config.base.frequency == '1d' and not self._match_immediately:
            self._delayed_orders.append((account, order))
            return

        self._open_orders.append((account, order))
        order._active()
        self._env.event_bus.publish_event(Events.ORDER_CREATION_PASS, account, order)
        if self._match_immediately:
            self._match()

    def cancel_order(self, order):
        account = self._get_account_for(order.order_book_id)
        account.on_order_cancelling(order)
        order._mark_cancelled(_("{order_id} order has been cancelled by user.").format(order_id=order.order_id))
        account.on_order_cancellation_pass(order)
        try:
            self._open_orders.remove((account, order))
        except ValueError:
            try:
                self._delayed_orders.remove((account, order))
            except ValueError:
                pass

    def before_trading(self):
        for account, order in self._open_orders:
            order._active()
            self._env.event_bus.publish_event(Events.ORDER_CREATION_PASS, account, order)

    def after_trading(self):
        for account, order in self._open_orders:
            order._mark_rejected(_("Order Rejected: {order_book_id} can not match. Market close.").format(
                order_book_id=order.order_book_id
            ))
            account.on_unsolicited_order_update(order)
        self._open_orders = self._delayed_orders
        self._delayed_orders = []

    def update(self, calendar_dt, trading_dt, bar_dict):
        self._matcher.update(calendar_dt, trading_dt, bar_dict)
        self._match()

    def _match(self):
        self._matcher.match(self._open_orders)
        final_orders = [(a, o) for a, o in self._open_orders if o._is_final()]
        self._open_orders = [(a, o) for a, o in self._open_orders if not o._is_final()]

        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED:
                account.on_unsolicited_order_update(order)
            elif order.status == ORDER_STATUS.CANCELLED:
                account.on_order_cancellation_pass(order)
