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
from rqalpha.utils.i18n import gettext as _
from rqalpha.events import EVENT, Event
from rqalpha.const import MATCHING_TYPE, ORDER_STATUS
from rqalpha.model.order import Order

from .matcher import Matcher
from .utils import init_portfolio


class SimulationBroker(AbstractBroker, Persistable):
    def __init__(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

        self._matcher = Matcher(env, mod_config)
        self._match_immediately = mod_config.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE

        self._open_orders = []
        self._delayed_orders = []
        self._frontend_validator = {}

        # 该事件会触发策略的before_trading函数
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # 该事件会触发策略的handle_bar函数
        self._env.event_bus.add_listener(EVENT.BAR, self.on_bar)
        # 该事件会触发策略的handel_tick函数
        self._env.event_bus.add_listener(EVENT.TICK, self.on_tick)
        # 该事件会触发策略的after_trading函数
        self._env.event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)

    def get_portfolio(self):
        return init_portfolio(self._env)

    def get_open_orders(self, order_book_id=None):
        if order_book_id is None:
            return [order for account, order in self._open_orders]
        else:
            return [order for account, order in self._open_orders if order.order_book_id == order_book_id]

    def get_state(self):
        return jsonpickle.dumps({
            'open_orders': [o.get_state() for account, o in self._open_orders],
            'delayed_orders': [o.get_state() for account, o in self._delayed_orders]
        }).encode('utf-8')

    def set_state(self, state):
        self._open_orders = []
        self._delayed_orders = []

        value = jsonpickle.loads(state.decode('utf-8'))
        for v in value['open_orders']:
            o = Order()
            o.set_state(v)
            account = self._env.get_account(o.order_book_id)
            self._open_orders.append((account, o))
        for v in value['delayed_orders']:
            o = Order()
            o.set_state(v)
            account = self._env.get_account(o.order_book_id)
            self._delayed_orders.append((account, o))

    def submit_order(self, order):
        account = self._env.get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        if order.is_final():
            return
        if self._env.config.base.frequency == '1d' and not self._match_immediately:
            self._delayed_orders.append((account, order))
            return
        self._open_orders.append((account, order))
        order.active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
        if self._match_immediately:
            self._match()

    def cancel_order(self, order):
        account = self._env.get_account(order.order_book_id)

        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_CANCEL, account=account, order=order))

        order.mark_cancelled(_(u"{order_id} order has been cancelled by user.").format(order_id=order.order_id))

        self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_PASS, account=account, order=order))

        try:
            self._open_orders.remove((account, order))
        except ValueError:
            try:
                self._delayed_orders.remove((account, order))
            except ValueError:
                pass

    def before_trading(self, event):
        for account, order in self._open_orders:
            order.active()
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))

    def after_trading(self, event):
        for account, order in self._open_orders:
            order.mark_rejected(_(u"Order Rejected: {order_book_id} can not match. Market close.").format(
                order_book_id=order.order_book_id
            ))
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
        self._open_orders = self._delayed_orders
        self._delayed_orders = []

    def on_bar(self, event):
        self._matcher.update(self._env.calendar_dt, self._env.trading_dt)
        self._match()

    def on_tick(self, event):
        tick = event.tick
        self._matcher.update(self._env.calendar_dt, self._env.trading_dt)
        self._match(tick.order_book_id)

    def _match(self, order_book_id=None):
        open_orders = self._open_orders
        if order_book_id is not None:
            open_orders = [(a, o) for (a, o) in self._open_orders if o.order_book_id == order_book_id]
        self._matcher.match(open_orders)
        final_orders = [(a, o) for a, o in self._open_orders if o.is_final()]
        self._open_orders = [(a, o) for a, o in self._open_orders if not o.is_final()]

        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED or order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
