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
import csv

from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT


class ProgressiveOutputCSVMod(AbstractMod):

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

        env.event_bus.add_listener(EVENT.POST_BAR, self._output_feeds)

        output_path = mod_config.output_path

        filename = os.path.join(output_path, "portfolio.csv")
        new_file = False
        if not os.path.exists(filename):
            new_file = True
        self.csv_file = open(filename, 'a')
        fieldnames = ["datetime", "portfolio_value", "market_value", "total_returns"]
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames)
        if new_file:
            self.csv_writer.writeheader()

    def _output_feeds(self, *args, **kwargs):
        misc_account = self._env.account
        calendar_date = self._env.calendar_dt.date()
        portfolio = misc_account.portfolio

        self.csv_writer.writerow({
            "datetime": calendar_date,
            "total_returns": portfolio.total_returns,
            "portfolio_value": portfolio.portfolio_value,
            "market_value": portfolio.market_value,
        })
        self.csv_file.flush()

    def tear_down(self, code, exception=None):
        pass
