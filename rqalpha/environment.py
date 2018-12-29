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

from rqalpha.events import EventBus
from rqalpha.utils import get_account_type
from rqalpha.utils.logger import system_log, user_log, user_detail_log
from rqalpha.utils.i18n import gettext as _


class Environment(object):
    _env = None

    def __init__(self, config):
        Environment._env = self
        self.config = config
        self._universe = None
        self.data_proxy = None
        self.data_source = None
        self.price_board = None
        self.event_source = None
        self.strategy_loader = None
        self.global_vars = None
        self.persist_provider = None
        self.persist_helper = None
        self.broker = None
        self.profile_deco = None
        self.system_log = system_log
        self.user_log = user_log
        self.user_detail_log = user_detail_log
        self.event_bus = EventBus()
        self.portfolio = None
        self.booking = None
        self.benchmark_provider = None
        self.benchmark_portfolio = None
        self.calendar_dt = None
        self.trading_dt = None
        self.mod_dict = None
        self.plot_store = None
        self.bar_dict = None
        self.user_strategy = None
        self._frontend_validators = []
        self._account_model_dict = {}
        self._position_model_dict = {}
        self._transaction_cost_decider_dict = {}

    @classmethod
    def get_instance(cls):
        """
        返回已经创建的 Environment 对象
        """
        if Environment._env is None:
            raise RuntimeError(
                _(u"Environment has not been created. Please Use `Environment.get_instance()` after RQAlpha init"))
        return Environment._env

    def set_data_proxy(self, data_proxy):
        self.data_proxy = data_proxy

    def set_data_source(self, data_source):
        self.data_source = data_source

    def set_price_board(self, price_board):
        self.price_board = price_board

    def set_strategy_loader(self, strategy_loader):
        self.strategy_loader = strategy_loader

    def set_global_vars(self, global_vars):
        self.global_vars = global_vars

    def set_hold_strategy(self):
        self.config.extra.is_hold = True

    def cancel_hold_strategy(self):
        self.config.extra.is_hold = False

    def set_persist_helper(self, helper):
        self.persist_helper = helper

    def set_persist_provider(self, provider):
        self.persist_provider = provider

    def set_event_source(self, event_source):
        self.event_source = event_source

    def set_broker(self, broker):
        self.broker = broker

    def add_frontend_validator(self, validator):
        self._frontend_validators.append(validator)

    def set_account_model(self, account_type, account_model):
        self._account_model_dict[account_type] = account_model

    def get_account_model(self, account_type):
        if account_type not in self._account_model_dict:
            raise RuntimeError(_(u"Unknown Account Type {}").format(account_type))
        return self._account_model_dict[account_type]

    def set_position_model(self, account_type, position_model):
        self._position_model_dict[account_type] = position_model

    def get_position_model(self, account_type):
        if account_type not in self._position_model_dict:
            raise RuntimeError(_(u"Unknown Account Type {}").format(account_type))
        return self._position_model_dict[account_type]

    def can_submit_order(self, order):
        if Environment.get_instance().config.extra.is_hold:
            return False
        try:
            account = self.get_account(order.order_book_id)
        except NotImplementedError:
            account = None
        for v in self._frontend_validators:
            if not v.can_submit_order(order, account):
                return False
        return True

    def can_cancel_order(self, order):
        if order.is_final():
            return False
        try:
            account = self.get_account(order.order_book_id)
        except NotImplementedError:
            account = None
        for v in self._frontend_validators:
            if not v.can_cancel_order(order, account):
                return False
        return True

    def set_bar_dict(self, bar_dict):
        self.bar_dict = bar_dict

    def get_universe(self):
        return self._universe.get()

    def update_universe(self, universe):
        self._universe.update(universe)

    def get_plot_store(self):
        if self.plot_store is None:
            from rqalpha.utils.plot_store import PlotStore
            self.plot_store = PlotStore()
        return self.plot_store

    def add_plot(self, series_name, value):
        self.get_plot_store().add_plot(self.trading_dt.date(), series_name, value)

    def get_bar(self, order_book_id):
        return self.bar_dict[order_book_id]

    def get_last_price(self, order_book_id):
        return self.data_proxy.get_last_price(order_book_id)

    def get_instrument(self, order_book_id):
        return self.data_proxy.instruments(order_book_id)

    def get_account_type(self, order_book_id):
        # 如果新的account_type 可以通过重写该函数来进行扩展
        return get_account_type(order_book_id)

    def get_account(self, order_book_id):
        if not self.portfolio:
            raise NotImplementedError
        account_type = get_account_type(order_book_id)
        return self.portfolio.accounts[account_type]

    def get_open_orders(self, order_book_id=None):
        return self.broker.get_open_orders(order_book_id)

    def set_transaction_cost_decider(self, account_type, decider):
        self._transaction_cost_decider_dict[account_type] = decider

    def _get_transaction_cost_decider(self, account_type):
        try:
            return self._transaction_cost_decider_dict[account_type]
        except KeyError:
            raise NotImplementedError(_(u"No such transaction cost decider for such account_type {}.".format(
                account_type
            )))

    def get_trade_tax(self, account_type, trade):
        return self._get_transaction_cost_decider(account_type).get_trade_tax(trade)

    def get_trade_commission(self, account_type, trade):
        return self._get_transaction_cost_decider(account_type).get_trade_commission(trade)

    def get_order_transaction_cost(self, account_type, order):
        return self._get_transaction_cost_decider(account_type).get_order_transaction_cost(order)

    def set_benchmark_provider(self, benchmark_provider):
        self.benchmark_provider = benchmark_provider
