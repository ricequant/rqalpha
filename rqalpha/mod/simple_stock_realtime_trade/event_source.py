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
import threading
from threading import Thread

from six.moves.queue import Queue

from rqalpha.interface import AbstractEventSource
from rqalpha.environment import Environment
from rqalpha.utils.logger import system_log
from rqalpha.events import Events


class RealtimeEventSource(AbstractEventSource):
    def __init__(self):
        self._env = Environment.get_instance()
        self.fps = 3
        self.event_queue = Queue()
        self.clock_engine_thread = Thread(target=self.clock_worker)
        self.clock_engine_thread.daemon = True
        self.clock_engine_thread.start()

    def clock_worker(self):
        while True:
            time.sleep(self.fps)
            dt = datetime.datetime.now()
            system_log.debug("put event {}", dt)
            self.event_queue.put(dt)

    def events(self, start_date, end_date, frequency):
        running = True
        count = 0

        while running:
            count += 1

            real_dt = datetime.datetime.now()
            dt = self.event_queue.get()

            system_log.debug("real_dt {}, dt {}", real_dt, dt)
            yield dt, dt, Events.BAR

            if count % 10 == 0:
                yield dt, dt, Events.AFTER_TRADING

            time.sleep(1)
