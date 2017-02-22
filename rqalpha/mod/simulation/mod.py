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

from rqalpha.interface import AbstractMod

from .simulation_broker import SimulationBroker
from .simulation_event_source import SimulationEventSource


class SimulationMod(AbstractMod):
    def __init__(self):
        self._env = None

    def start_up(self, env, mod_config):
        self._env = env
        self._env.set_broker(SimulationBroker(self._env))

        event_source = SimulationEventSource(env, env.config.base.account_list)
        env.set_event_source(event_source)

    def tear_down(self, code, exception=None):
        pass
