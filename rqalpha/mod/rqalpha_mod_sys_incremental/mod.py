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
import datetime

from rqalpha.utils.logger import system_log
from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT
from rqalpha.const import PERSIST_MODE
from rqalpha.utils.disk_persist_provider import DiskPersistProvider
from rqalpha.utils.i18n import gettext as _

from . import recorders


class IncrementalMod(AbstractMod):
    def __init__(self):
        self._env = None

    def start_up(self, env, mod_config):
        self._env = env
        self._recorder = None

        env.config.base.persist = True
        env.config.base.persist_mode = PERSIST_MODE.ON_NORMAL_EXIT

        self._meta = {
            "strategy_id": mod_config.strategy_id,
            "origin_start_date": self._env.config.base.start_date.strftime("%Y-%m-%d"),
            "start_date": self._env.config.base.start_date.strftime("%Y-%m-%d"),
            "end_date": self._env.config.base.end_date.strftime("%Y-%m-%d"),
            "last_run_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if mod_config.use_disk_persist_provider:
            persist_provider = DiskPersistProvider(os.path.join(mod_config.persist_folder, "persist"))
            env.set_persist_provider(persist_provider)

        recorder_cls = getattr(recorders, mod_config.recorder)
        self._recorder = recorder_cls(mod_config)

        persist_meta = self._recorder.load_meta()
        if persist_meta:
            if persist_meta["end_date"] >= self._meta["start_date"]:
                raise RuntimeError(
                    _(u"current start_date {} is before last end_date {}").format(
                        self._meta["start_date"], persist_meta["end_date"]))
            else:
                self._meta["origin_start_date"] = persist_meta["origin_start_date"]

        env.event_bus.add_listener(EVENT.TRADE, self.on_trade)
        env.event_bus.add_listener(EVENT.POST_SETTLEMENT, self.on_settlement)

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
            if self._recorder:
                self._recorder.store_meta(self._meta)
                self._recorder.flush()
                self._recorder.close()
