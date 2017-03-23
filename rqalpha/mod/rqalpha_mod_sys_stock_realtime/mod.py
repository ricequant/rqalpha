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
from rqalpha.utils.disk_persist_provider import DiskPersistProvider
from rqalpha.const import RUN_TYPE, PERSIST_MODE

from .data_source import DataSource
from .event_source import RealtimeEventSource


class RealtimeTradeMod(AbstractMod):

    def start_up(self, env, mod_config):

        if env.config.base.run_type == RUN_TYPE.PAPER_TRADING:
            env.set_data_source(DataSource(env.config.base.data_bundle_path))
            env.set_event_source(RealtimeEventSource(mod_config.fps))

            persist_provider = DiskPersistProvider(mod_config.persist_path)
            env.set_persist_provider(persist_provider)

            env.config.base.persist = True
            env.config.base.persist_mode = PERSIST_MODE.REAL_TIME

    def tear_down(self, code, exception=None):
        pass
