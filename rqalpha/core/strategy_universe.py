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
import json
import copy

from rqalpha.events import EVENT, Event
from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument


class StrategyUniverse(object):
    def __init__(self):
        self._set = set()
        Environment.get_instance().event_bus.prepend_listener(EVENT.AFTER_TRADING, self._clear_de_listed)

    def get_state(self):
        return json.dumps(sorted(self._set)).encode('utf-8')

    def set_state(self, state):
        l = json.loads(state.decode('utf-8'))
        self.update(l)

    def update(self, universe):
        if isinstance(universe, (six.string_types, Instrument)):
            universe = [universe]
        new_set = set(universe)
        if new_set != self._set:
            self._set = new_set
            Environment.get_instance().event_bus.publish_event(Event(EVENT.POST_UNIVERSE_CHANGED, universe=self._set))

    def get(self):
        return copy.copy(self._set)

    def _clear_de_listed(self, event):
        de_listed = set()
        env = Environment.get_instance()
        for o in self._set:
            i = env.data_proxy.instruments(o)
            if i.de_listed_date <= env.trading_dt:
                de_listed.add(o)
        if de_listed:
            self._set -= de_listed
            env.event_bus.publish_event(Event(EVENT.POST_UNIVERSE_CHANGED, universe=self._set))
