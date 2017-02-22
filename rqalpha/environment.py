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

from .utils.logger import system_log, user_log, user_detail_log
from .events import EVENT, EventBus
from .model.commission import init_commission


class Environment(object):
    _env = None

    def __init__(self, config):
        Environment._env = self
        self._config = config
        self._data_proxy = None
        self._data_source = None
        self._event_source = None
        self._strategy_loader = None
        self._global_vars = None
        self._persist_provider = None
        self._commission_initializer = init_commission
        self.system_log = system_log
        self.user_log = user_log
        self.user_detail_log = user_detail_log
        self.event_bus = EventBus()
        self._broker = None
        self.account = None
        self.accounts = None
        self.calendar_dt = None
        self.trading_dt = None
        self.mod_dict = None
        self._universe = None
        self.profile_deco = None

    @classmethod
    def get_instance(cls):
        return Environment._env

    @property
    def config(self):
        return self._config

    def set_data_proxy(self, data_proxy):
        self._data_proxy = data_proxy

    @property
    def data_proxy(self):
        return self._data_proxy

    def set_data_source(self, data_source):
        self._data_source = data_source

    @property
    def data_source(self):
        return self._data_source

    @property
    def strategy_loader(self):
        return self._strategy_loader

    def set_strategy_loader(self, strategy_loader):
        self._strategy_loader = strategy_loader

    @property
    def global_vars(self):
        return self._global_vars

    def set_global_vars(self, global_vars):
        self._global_vars = global_vars

    def set_hold_strategy(self):
        self.config.extra.is_hold = True

    def cancel_hold_strategy(self):
        self.config.extra.is_hold = False

    @property
    def is_strategy_hold(self):
        return self.config.extra.is_hold

    def set_persist_provider(self, provider):
        self._persist_provider = provider

    @property
    def persist_provider(self):
        return self._persist_provider

    def set_event_source(self, event_source):
        self._event_source = event_source

    @property
    def event_source(self):
        return self._event_source

    @property
    def broker(self):
        return self._broker

    def set_broker(self, broker):
        self._broker = broker

    @property
    def universe(self):
        return self._universe.get()

    def update_universe(self, universe):
        self._universe.update(universe)
        self.event_bus.publish_event(EVENT.POST_UNIVERSE_CHANGED, universe)
