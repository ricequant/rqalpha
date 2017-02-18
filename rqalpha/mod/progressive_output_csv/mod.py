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

from six import StringIO

from rqalpha.interface import AbstractMod
from rqalpha.utils.logger import system_log
from rqalpha.events import Events


class ProgressiveOutputCSVMod(AbstractMod):

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

        env.event_bus.add_listener(Events.TRADE, self._output_trade)
        env.event_bus.add_listener(Events.POST_BAR, self._output_feeds)

        self._csv_txt = StringIO()
        output_path = mod_config.output_path

        self.csv_file = open(os.path.join(output_path, "feeds.csv"), 'a')

    def _output_trade(self, account, trade):
        pass

    def _output_feeds(self, *args, **kwargs):
        misc_account = self._env.account
        # trading_date = self._env.trading_dt.date()
        calendar_date = self._env.calendar_dt.date()
        portfolio = misc_account.portfolio
        # daily_return = portfolio.daily_returns

        output_txt = "{} {}\n".format(calendar_date, portfolio)
        self.csv_file.write(output_txt)
        self.csv_file.flush()

    def tear_down(self, code, exception=None):
        pass
