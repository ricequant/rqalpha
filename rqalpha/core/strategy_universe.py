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

import json

import six

from ..events import EVENT
from ..environment import Environment
from ..model.instrument import Instrument


class StrategyUniverse(object):
    def __init__(self):
        self._set = set()
        Environment.get_instance().event_bus.add_listener(EVENT.AFTER_TRADING, self._clear_de_listed)

    def get_state(self):
        return json.dumps(sorted(self._set)).encode('utf-8')

    def set_state(self, state):
        l = json.loads(state.decode('utf-8'))
        self.update(l)

    def update(self, universe):
        if isinstance(universe, (six.string_types, Instrument)):
            universe = [universe]
        self._set = set(universe)
        Environment.get_instance().event_bus.publish_event(EVENT.POST_UNIVERSE_CHANGED, self._set)

    def get(self):
        return self._set

    def _clear_de_listed(self):
        de_listed = set()
        for o in self._set:
            i = Environment.get_instance().data_proxy.instruments(o)
            if i.de_listed_date <= Environment.get_instance().trading_dt:
                de_listed.add(o)
        if de_listed:
            self._set -= de_listed
            Environment.get_instance().event_bus.publish_event(EVENT.POST_UNIVERSE_CHANGED, self._set)
