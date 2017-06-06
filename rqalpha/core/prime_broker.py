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

from ..model.portfolio import Portfolio


class PrimeBroker(object):
    def __init__(self, env):
        self.env = env
        self.broker_dict = dict()
        self.accounts = dict()

    def register_broker(self, broker_type, broker):
        self.broker_dict[broker_type] = broker

    def after_trading(self):
        for broker in self.broker_dict.values():
            broker.after_trading()

    def before_trading(self):
        for broker in self.broker_dict.values():
            broker.before_trading()

    def get_open_orders(self, order_book_id=None):
        if order_book_id is not None:
            broker_type = self.env.get_account_type(order_book_id)
            return self.broker_dict[broker_type].get_open_orders(order_book_id)
        else:
            orders = []
            for broker in self.broker_dict.values():
                orders += broker.get_open_orders()
            return orders

    def submit_order(self, order):
        broker_type = self.env.get_account_type(order.order_book_id)
        return self.broker_dict[broker_type].submit_order(order)

    def cancel_order(self, order):
        broker_type = self.env.get_account_type(order.order_book_id)
        return self.broker_dict[broker_type].cancel_order(order)

    def get_portfolio(self):
        config = self.env.config
        start_date = config.base.start_date
        total_cash = 0
        for account_type in config.base.account_list:
            self.accounts[account_type] = self.broker_dict[account_type].get_account()
            total_cash += self.accounts[account_type].cash
        return Portfolio(start_date, 1, total_cash, self.accounts)
