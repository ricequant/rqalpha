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
from rqalpha.events import EVENT

from .stat import Stat


class StatMod(AbstractMod):
    def __init__(self):
        self._env = None
        self._mod_config = None
        self._stat = Stat()
        self._inject_api()

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

        env.event_bus.add_listener(EVENT.TRADE, self._stat.handle_trade)

    def tear_down(self, code, exception=None):
        pass

    def _inject_api(self):
        from rqalpha import export_as_api
        from rqalpha.execution_context import ExecutionContext
        from rqalpha.const import EXECUTION_PHASE

        @export_as_api
        @ExecutionContext.enforce_phase(
            EXECUTION_PHASE.BEFORE_TRADING,
            EXECUTION_PHASE.ON_BAR,
            EXECUTION_PHASE.AFTER_TRADING,
            EXECUTION_PHASE.SCHEDULED)
        def get_stat():
            return self._stat
