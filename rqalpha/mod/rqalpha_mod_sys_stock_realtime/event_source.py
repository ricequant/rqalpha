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
from rqalpha.utils import rq_json
from rqalpha.utils.i18n import gettext as _
from .utils import get_realtime_quotes, is_holiday_today, is_tradetime_now
from . import data_board


class RealtimeEventSource(AbstractEventSource):
    MARKET_DATA_EVENT = "RealtimeEventSource.MARKET_DATA_EVENT"

    def __init__(self, fps, mod_config):
        self._env = Environment.get_instance()
        self.mod_config = mod_config
        self.fps = fps
        self.event_queue = Queue()

        self.before_trading_fire_date = datetime.date(2000, 1, 1)
        self.after_trading_fire_date = datetime.date(2000, 1, 1)
        self.settlement_fire_date = datetime.date(2000, 1, 1)

        if not mod_config.redis_uri:
            self.quotation_engine_thread = Thread(target=self.quotation_worker)
            self.quotation_engine_thread.daemon = True

        self.clock_engine_thread = Thread(target=self.clock_worker)
        self.clock_engine_thread.daemon = True

    def set_state(self, state):
        persist_dict = rq_json.convert_json_to_dict(state.decode('utf-8'))
        self.before_trading_fire_date = persist_dict['before_trading_fire_date']
        self.after_trading_fire_date = persist_dict['after_trading_fire_date']
        self.settlement_fire_date = persist_dict['settlement_fire_date']

    def get_state(self):
        return rq_json.convert_dict_to_json({
            "before_trading_fire_date": self.before_trading_fire_date,
            "after_trading_fire_date": self.after_trading_fire_date,
            "settlement_fire_date": self.settlement_fire_date,
        }).encode('utf-8')

    def quotation_worker(self):
        while True:
            if not is_holiday_today() and is_tradetime_now():
                order_book_id_list = sorted([instruments.order_book_id for instruments in self._env.data_proxy.all_instruments("CS", self._env.trading_dt)])
                try:
                    data_board.realtime_quotes_df = get_realtime_quotes(order_book_id_list)
                except Exception as e:
                    system_log.exception(_("get_realtime_quotes fail"))
                    continue

            time.sleep(1)

    def clock_worker(self):
        data_proxy = self._env.data_proxy

        while True:
            # wait for the first data ready
            if data_proxy.current_snapshot("000001.XSHG", None, None).datetime.date() == datetime.date.today():
                system_log.info(_("Market data is ready, start to work now!"))
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

        if not self.mod_config.redis_uri:
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
            yield Event(event_type, calendar_dt=real_dt, trading_dt=dt)
