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

from .events import EventBus
from .utils import get_upper_underlying_symbol, get_account_type
from .utils.logger import system_log, user_log, user_detail_log
from .utils.default_future_info import DEFAULT_FUTURE_INFO


class Environment(object):
    _env = None

    def __init__(self, config):
        Environment._env = self
        self.config = config
        self._universe = None
        self.data_proxy = None
        self.data_source = None
        self.event_source = None
        self.strategy_loader = None
        self.global_vars = None
        self.persist_provider = None
        self.broker = None
        self.profile_deco = None
        self.system_log = system_log
        self.user_log = user_log
        self.user_detail_log = user_detail_log
        self.event_bus = EventBus()
        self.portfolio = None
        self.calendar_dt = None
        self.trading_dt = None
        self.mod_dict = None
        self.plot_store = None
        self.bar_dict = None

    @classmethod
    def get_instance(cls):
        return Environment._env

    def set_data_proxy(self, data_proxy):
        self.data_proxy = data_proxy

    def set_data_source(self, data_source):
        self.data_source = data_source

    def set_strategy_loader(self, strategy_loader):
        self.strategy_loader = strategy_loader

    def set_global_vars(self, global_vars):
        self.global_vars = global_vars

    def set_hold_strategy(self):
        self.config.extra.is_hold = True

    def cancel_hold_strategy(self):
        self.config.extra.is_hold = False

    def set_persist_provider(self, provider):
        self.persist_provider = provider

    def set_event_source(self, event_source):
        self.event_source = event_source

    def set_broker(self, broker):
        self.broker = broker

    def set_bar_dict(self, bar_dict):
        self.bar_dict = bar_dict

    def get_universe(self):
        return self._universe.get()

    def update_universe(self, universe):
        self._universe.update(universe)

    def get_plot_store(self):
        if self.plot_store is None:
            from .utils.plot_store import PlotStore
            self.plot_store = PlotStore()
        return self.plot_store

    def add_plot(self, series_name, value):
        self.get_plot_store().add_plot(self.trading_dt.date(), series_name, value)

    def get_bar(self, order_book_id):
        return self.bar_dict[order_book_id]

    def get_last_price(self, order_book_id):
        return self.data_proxy.current_snapshot(
            order_book_id,
            self.config.base.frequency,
            self.calendar_dt
        ).last

    def get_instrument(self, order_book_id):
        return self.data_proxy.instruments(order_book_id)

    def get_future_commission_info(self, order_book_id, hedge_type):
        try:
            return self.data_proxy.get_future_info(order_book_id, hedge_type)
        except NotImplementedError:
            underlying_symbol = get_upper_underlying_symbol(order_book_id)
            return DEFAULT_FUTURE_INFO[underlying_symbol][hedge_type.value]

    def get_future_margin_rate(self, order_book_id):
        try:
            return self.data_proxy.get_future_info(order_book_id)['long_margin_ratio']
        except NotImplementedError:
            return self.data_proxy.instruments(order_book_id).margin_rate

    def get_future_info(self, order_book_id, hedge_type):
        return self.data_proxy.get_future_info(order_book_id, hedge_type)

    def get_account(self, order_book_id):
        account_type = get_account_type(order_book_id)
        return self.portfolio.accounts[account_type]

    def get_open_orders(self, order_book_id=None):
        return self.broker.get_open_orders(order_book_id)
