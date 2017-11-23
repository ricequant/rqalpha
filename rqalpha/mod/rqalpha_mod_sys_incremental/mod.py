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

import os
import json

from rqalpha.utils.logger import system_log
from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT
from rqalpha.const import PERSIST_MODE
from rqalpha.utils.disk_persist_provider import DiskPersistProvider
from rqalpha.utils.i18n import gettext as _

from .recorder import CsvRecorder


class IncrementalMod(AbstractMod):
    def __init__(self):
        self._env = None

    def start_up(self, env, mod_config):
        self._env = env
        self._recorder = None

        env.config.base.persist = True
        env.config.base.persist_mode = PERSIST_MODE.ON_NORMAL_EXIT

        self._meta_json_path = os.path.join(mod_config.persist_folder, "meta.json")
        self._meta = {
            "start_date": self._env.config.base.start_date.strftime("%Y-%m-%d"),
            "end_date": self._env.config.base.end_date.strftime("%Y-%m-%d"),
        }
        if not os.path.exists(self._meta_json_path):
            self._meta["origin_start_date"] = self._meta["start_date"]
        else:
            with open(self._meta_json_path, "r") as json_file:
                persist_meta = json.load(json_file)
            self._meta["origin_start_date"] = persist_meta["origin_start_date"]

            if self._meta["start_date"] <= persist_meta["end_date"]:
                raise RuntimeError(
                    _(u"current start_date {} is before last end_date {}").format(self._meta["start_date"],
                                                                                  persist_meta["end_date"]))

        if mod_config.use_disk_persist:
            persist_provider = DiskPersistProvider(os.path.join(mod_config.persist_folder, "persist"))
            env.set_persist_provider(persist_provider)

        if mod_config.use_csv_feeds_record:
            self._recorder = CsvRecorder(mod_config.persist_folder)

        if self._recorder:
            env.event_bus.add_listener(EVENT.TRADE, self.on_trade)
            env.event_bus.add_listener(EVENT.SETTLEMENT, self.on_settlement)

    def on_trade(self, event):
        trade = event.trade
        self._recorder.append_trade(trade)

    def on_settlement(self, event):
        calendar_dt = self._env.calendar_dt
        portfolio = self._env.portfolio
        bm_portfolio = self._env.benchmark_portfolio
        self._recorder.append_portfolio(calendar_dt, portfolio, bm_portfolio)

    def tear_down(self, success, exception=None):
        if exception is None:
            # 仅当成功运行才写入数据
            with open(self._meta_json_path, "w") as json_file:
                json_file.write(json.dumps(self._meta))

            if self._recorder:
                self._recorder.flush()
                self._recorder.close()
