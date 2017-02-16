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

import datetime
import time

from rqalpha.interface import AbstractEventSource
from rqalpha.environment import Environment
from rqalpha.utils.logger import system_log
from rqalpha.events import Events


class RealtimeEventSource(AbstractEventSource):
    def __init__(self):
        self._env = Environment.get_instance()

    def events(self, start_date, end_date, frequency):
        running = True
        count = 0
        while running:
            count += 1
            dt = datetime.datetime.now()
            system_log.info("dt {}", dt)
            yield dt, dt, Events.BAR
            if count % 10 == 0:
                yield dt, dt, Events.AFTER_TRADING

            time.sleep(1)
