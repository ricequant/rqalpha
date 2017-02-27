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

import jsonpickle

from rqalpha.interface import AbstractBroker, Persistable
from rqalpha.utils import get_account_type
from rqalpha.utils.i18n import gettext as _
from rqalpha.events import EVENT
from rqalpha.const import MATCHING_TYPE, ORDER_STATUS
from rqalpha.const import ACCOUNT_TYPE
from rqalpha.environment import Environment
from rqalpha.model.account import BenchmarkAccount, StockAccount, FutureAccount

from .matcher import Matcher


def init_accounts(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    total_cash = 0
    for account_type in config.base.account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            stock_starting_cash = config.base.stock_starting_cash
            accounts[ACCOUNT_TYPE.STOCK] = StockAccount(env, stock_starting_cash, start_date)
            total_cash += stock_starting_cash
        elif account_type == ACCOUNT_TYPE.FUTURE:
            future_starting_cash = config.base.future_starting_cash
            accounts[ACCOUNT_TYPE.FUTURE] = FutureAccount(env, future_starting_cash, start_date)
            total_cash += future_starting_cash
        else:
            raise NotImplementedError
    if config.base.benchmark is not None:
        accounts[ACCOUNT_TYPE.BENCHMARK] = BenchmarkAccount(env, total_cash, start_date)

    return accounts


class SimulationBroker(AbstractBroker, Persistable):
    def __init__(self, env):
        self._env = env
        if env.config.base.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE:
            self._matcher = Matcher(lambda bar: bar.close, env.config.validator.bar_limit)
            self._match_immediately = True
        else:
            self._matcher = Matcher(lambda bar: bar.open, env.config.validator.bar_limit)
            self._match_immediately = False

        self._accounts = None
        self._open_orders = []
        self._board = None
        self._turnover = {}
        self._delayed_orders = []
        self._frontend_validator = {}

        # 该事件会触发策略的before_trading函数
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # 该事件会触发策略的handle_bar函数
        self._env.event_bus.add_listener(EVENT.BAR, self.bar)
        # 该事件会触发策略的handel_tick函数
        self._env.event_bus.add_listener(EVENT.TICK, self.tick)
        # 该事件会触发策略的after_trading函数
        self._env.event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)

    def get_accounts(self):
        if self._accounts is None:
            self._accounts = init_accounts(self._env)
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

    def submit_order(self, order):
        account = self._get_account_for(order.order_book_id)

        self._env.event_bus.publish_event(EVENT.ORDER_PENDING_NEW, account, order)

        account.append_order(order)
        if order._is_final():
            return

        # account.on_order_creating(order)
        if self._env.config.base.frequency == '1d' and not self._match_immediately:
            self._delayed_orders.append((account, order))
            return

        self._open_orders.append((account, order))
        order._active()
        self._env.event_bus.publish_event(EVENT.ORDER_CREATION_PASS, account, order)
        if self._match_immediately:
            self._match()

    def cancel_order(self, order):
        account = self._get_account_for(order.order_book_id)

        self._env.event_bus.publish_event(EVENT.ORDER_PENDING_CANCEL, account, order)

        # account.on_order_cancelling(order)
        order._mark_cancelled(_("{order_id} order has been cancelled by user.").format(order_id=order.order_id))

        self._env.event_bus.publish_event(EVENT.ORDER_CANCELLATION_PASS, account, order)

        # account.on_order_cancellation_pass(order)
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
            self._env.event_bus.publish_event(EVENT.ORDER_CREATION_PASS, account, order)

    def after_trading(self):
        for account, order in self._open_orders:
            order._mark_rejected(_("Order Rejected: {order_book_id} can not match. Market close.").format(
                order_book_id=order.order_book_id
            ))
            self._env.event_bus.publish_event(EVENT.ORDER_UNSOLICITED_UPDATE, account, order)
        self._open_orders = self._delayed_orders
        self._delayed_orders = []

    def bar(self, bar_dict):
        env = Environment.get_instance()
        self._matcher.update(env.calendar_dt, env.trading_dt, bar_dict)
        self._match()

    def tick(self, tick):
        # TODO support tick matching
        pass
        # env = Environment.get_instance()
        # self._matcher.update(env.calendar_dt, env.trading_dt, tick)
        # self._match()

    def _match(self):
        self._matcher.match(self._open_orders)
        final_orders = [(a, o) for a, o in self._open_orders if o._is_final()]
        self._open_orders = [(a, o) for a, o in self._open_orders if not o._is_final()]

        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED:
                self._env.event_bus.publish_event(EVENT.ORDER_UNSOLICITED_UPDATE, account, order)
            elif order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(EVENT.ORDER_CANCELLATION_PASS, account, order)
