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
from threading import Thread

from six.moves.queue import Queue, Empty

from rqalpha.interface import AbstractEventSource
from rqalpha.environment import Environment
from rqalpha.utils.logger import system_log
from rqalpha.events import Event, EVENT
from rqalpha.execution_context import ExecutionContext
from rqalpha.utils import json as json_utils
from .utils import get_realtime_quotes, order_book_id_2_tushare_code, is_holiday_today, is_tradetime_now


class RealtimeEventSource(AbstractEventSource):

    def __init__(self, fps):
        self._env = Environment.get_instance()
        self.fps = fps
        self.event_queue = Queue()

        self.before_trading_fire_date = datetime.date(2000, 1, 1)
        self.after_trading_fire_date = datetime.date(2000, 1, 1)

        self.clock_engine_thread = Thread(target=self.clock_worker)
        self.clock_engine_thread.daemon = True

        self.quotation_engine_thread = Thread(target=self.quotation_worker)
        self.quotation_engine_thread.daemon = True

    def set_state(self, state):
        persist_dict = json_utils.convert_json_to_dict(state.decode('utf-8'))
        self.before_trading_fire_date = persist_dict['before_trading_fire_date']
        self.after_trading_fire_date = persist_dict['after_trading_fire_date']

    def get_state(self):
        return json_utils.convert_dict_to_json({
            "before_trading_fire_date": self.before_trading_fire_date,
            "after_trading_fire_date": self.after_trading_fire_date,
        }).encode('utf-8')

    def quotation_worker(self):
        while True:
            if not is_holiday_today() and is_tradetime_now():
                order_book_id_list = sorted(ExecutionContext.data_proxy.all_instruments("CS").order_book_id.tolist())
                code_list = [order_book_id_2_tushare_code(code) for code in order_book_id_list]

                try:
                    self._env.data_source.realtime_quotes_df = get_realtime_quotes(code_list)
                except Exception as e:
                    system_log.exception("get_realtime_quotes fail")
                    continue

            time.sleep(1)

    def clock_worker(self):
        while True:
            # wait for the first data ready
            if not self._env.data_source.realtime_quotes_df.empty:
                break
            time.sleep(0.1)

        while True:
            time.sleep(self.fps)

            if is_holiday_today():
                time.sleep(60)
                continue

            dt = datetime.datetime.now()

            if dt.strftime("%H:%M:%S") >= "08:30:00" and dt.date() > self.before_trading_fire_date:
                self.event_queue.put((dt, EVENT.BEFORE_TRADING))
                self.before_trading_fire_date = dt.date()
            elif dt.strftime("%H:%M:%S") >= "15:10:00" and dt.date() > self.after_trading_fire_date:
                self.event_queue.put((dt, EVENT.AFTER_TRADING))
                self.after_trading_fire_date = dt.date()

            if is_tradetime_now():
                self.event_queue.put((dt, EVENT.BAR))

    def events(self, start_date, end_date, frequency):
        running = True

        self.clock_engine_thread.start()
        self.quotation_engine_thread.start()

        while running:
            real_dt = datetime.datetime.now()
            while True:
                try:
                    dt, event_type = self.event_queue.get(timeout=1)
                    break
                except Empty:
                    continue

            system_log.debug("real_dt {}, dt {}, event {}", real_dt, dt, event_type)
            yield Event(event_type, real_dt, dt)
