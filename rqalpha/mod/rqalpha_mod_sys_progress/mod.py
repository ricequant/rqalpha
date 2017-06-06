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

import click

from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT


class ProgressMod(AbstractMod):
    def __init__(self):
        self._show = False
        self._progress_bar = None
        self._trading_length = 0
        self._env = None

    def start_up(self, env, mod_config):
        self._show = mod_config.show
        self._env = env
        if self._show:
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._init)
            env.event_bus.add_listener(EVENT.POST_AFTER_TRADING, self._tick)

    def _init(self, event):
        self._trading_length = len(self._env.config.base.trading_calendar)
        self.progress_bar = click.progressbar(length=self._trading_length, show_eta=False)

    def _tick(self, event):
        self.progress_bar.update(1)

    def tear_down(self, success, exception=None):
        if self._show:
            self.progress_bar.render_finish()

