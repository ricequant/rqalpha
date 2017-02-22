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
from collections import OrderedDict

from ..portfolio import init_portfolio
from ..slippage import init_slippage
from ..tax import init_tax
from ..trade import Trade
from ..order import Order
from ...execution_context import ExecutionContext
from ...interface import Persistable
from ...utils import json as json_utils
from ...events import EVENT


class BaseAccount(Persistable):
    def __init__(self, env, init_cash, start_date, account_type):
        self._account_type = account_type
        self._env = env
        self.config = env.config

        self.portfolio = init_portfolio(init_cash, start_date, account_type)
        self.slippage_decider = init_slippage(env.config.base.slippage)
        commission_initializer = env._commission_initializer
        self.commission_decider = commission_initializer(self._account_type, env.config.base.commission_multiplier)
        self.tax_decider = init_tax(self._account_type)

        self.all_portfolios = OrderedDict()
        self.daily_orders = {}
        self.daily_trades = []

        # 该事件会触发策略的before_trading函数
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # 该事件会触发策略的handle_bar函数
        self._env.event_bus.add_listener(EVENT.BAR, self.bar)
        # 该事件会触发策略的handel_tick函数
        self._env.event_bus.add_listener(EVENT.TICK, self.tick)
        # 该事件会触发策略的after_trading函数
        self._env.event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)
        # 触发结算事件
        self._env.event_bus.add_listener(EVENT.SETTLEMENT, self.settlement)

        # 创建订单
        self._env.event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self.order_pending_new)
        # 创建订单成功
        self._env.event_bus.add_listener(EVENT.ORDER_CREATION_PASS, self.order_creation_pass)
        # 创建订单失败
        self._env.event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self.order_creation_reject)
        # 创建撤单
        self._env.event_bus.add_listener(EVENT.ORDER_PENDING_CANCEL, self.order_pending_cancel)
        # 撤销订单成功
        self._env.event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self.order_cancellation_pass)
        # 撤销订单失败
        self._env.event_bus.add_listener(EVENT.ORDER_CANCELLATION_REJECT, self.order_cancellation_reject)
        # 订单状态更新
        self._env.event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self.order_unsolicited_update)
        # 成交
        self._env.event_bus.add_listener(EVENT.TRADE, self.trade)

    def set_state(self, state):
        persist_dict = json_utils.convert_json_to_dict(state.decode('utf-8'))
        self.portfolio.restore_from_dict_(persist_dict['portfolio'])

        del self.daily_trades[:]
        self.daily_orders.clear()

        for order_id, order_dict in six.iteritems(persist_dict["daily_orders"]):
            self.daily_orders[order_id] = Order.__from_dict__(order_dict)

        for trade_dict in persist_dict["daily_trades"]:
            trade = Trade.__from_dict__(trade_dict, self.daily_orders[str(trade_dict["_order_id"])])
            self.daily_trades.append(trade)

    def get_state(self):
        return json_utils.convert_dict_to_json(self.__to_dict__()).encode('utf-8')

    def __to_dict__(self):
        account_dict = {
            "portfolio": self.portfolio.__to_dict__(),
            "daily_orders": {order_id: order.__to_dict__() for order_id, order in six.iteritems(self.daily_orders)},
            "daily_trades": [trade.__to_dict__() for trade in self.daily_trades],
        }
        return account_dict

    def portfolio_persist(self):
        trading_date = ExecutionContext.get_current_trading_dt().date()
        self.all_portfolios[trading_date] = self.portfolio._clone()

    def get_portfolio(self, trading_date):
        return self.all_portfolios[trading_date]

    def append_order(self, order, is_active=True):
        self.daily_orders[order.order_id] = order

    def append_trade(self, trade):
        self.daily_trades.append(trade)

    def get_open_orders(self):
        return {order.order_id: order for order in self.daily_orders.values() if order._is_active()}

    def get_order(self, order_id):
        return self.daily_orders.get(order_id, None)

    def before_trading(self):
        open_orders = {}
        for k, order in six.iteritems(self.daily_orders):
            if not order._is_final():
                open_orders[k] = order

        self.daily_orders = open_orders
        self.daily_trades = []

    def bar(self, bar_dict):
        pass

    def tick(self, tick):
        pass

    def after_trading(self):
        pass

    def settlement(self):
        pass

    def order_pending_new(self, account, order):
        pass

    def order_creation_pass(self, account, order):
        pass

    def order_creation_reject(self, account, order):
        pass

    def order_pending_cancel(self, account, order):
        pass

    def order_cancellation_pass(self, account, order):
        pass

    def order_cancellation_reject(self, account, order):
        pass

    def order_unsolicited_update(self, account, order):
        pass

    def trade(self, account, trade):
        pass
