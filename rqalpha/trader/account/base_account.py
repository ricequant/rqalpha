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

from six import iteritems
from collections import OrderedDict

from ...environment import Environment
from ...execution_context import ExecutionContext
from ...interface import Persistable
from ...model.portfolio import init_portfolio
from ...model.slippage import init_slippage
from ...model.tax import init_tax
from ...utils import json as json_utils
from ...model.trade import Trade
from ...model.order import Order


class BaseAccount(Persistable):
    def __init__(self, config, init_cash, start_date, account_type):
        self._account_type = account_type
        self.config = config

        self.portfolio = init_portfolio(init_cash, start_date, account_type)
        self.slippage_decider = init_slippage(config.base.slippage)
        commission_initializer = Environment.get_instance()._commission_initializer
        self.commission_decider = commission_initializer(self._account_type, config.base.commission_multiplier)
        self.tax_decider = init_tax(self._account_type)

        self.all_portfolios = OrderedDict()
        self.daily_orders = {}
        self.daily_trades = []

    def set_state(self, state):
        persist_dict = json_utils.convert_json_to_dict(state.decode('utf-8'))
        self.portfolio.restore_from_dict_(persist_dict['portfolio'])

        self.daily_orders.clear()
        self.daily_trades.clear()

        for order_id, order_dict in iteritems(persist_dict["daily_orders"]):
            self.daily_orders[order_id] = Order.__from_dict__(order_dict)

        for trade_dict in persist_dict["daily_trades"]:
            trade = Trade.__from_dict__(trade_dict, self.daily_orders[str(trade_dict["_order_id"])])
            self.daily_trades.append(trade)

    def get_state(self):
        return json_utils.convert_dict_to_json(self.__to_dict__()).encode('utf-8')

    def __to_dict__(self):
        account_dict = {
            "portfolio": self.portfolio.__to_dict__(),
            "daily_orders": {order_id: order.__to_dict__() for order_id, order in iteritems(self.daily_orders)},
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
        for k, order in self.daily_orders.items():
            if not order._is_final():
                open_orders[k] = order

        self.daily_orders = open_orders
        self.daily_trades = []

    def after_trading(self):
        pass

    def settlement(self):
        pass

    def on_bar(self, bar_dict):
        pass

    def on_order_creating(self, order):
        pass

    def on_order_creation_pass(self, order):
        pass

    def on_order_creation_reject(self, order):
        pass

    def on_order_cancelling(self, order):
        pass

    def on_order_cancellation_pass(self, order):
        pass

    def on_order_cancellation_reject(self, order):
        pass

    def on_order_trade(self, trade, bar_dict):
        pass

    def on_unsolicited_order_update(self, order):
        pass
