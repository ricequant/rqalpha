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

from rqalpha.events import EVENT, Event
from rqalpha.utils.rq_json import convert_dict_to_json, convert_json_to_dict

PRE_BEFORE_TRADING = Event(EVENT.PRE_BEFORE_TRADING)
POST_BEFORE_TRADING = Event(EVENT.POST_BEFORE_TRADING)
PRE_BAR = Event(EVENT.PRE_BAR)
POST_BAR = Event(EVENT.POST_BAR)
PRE_TICK = Event(EVENT.PRE_TICK)
POST_TICK = Event(EVENT.POST_TICK)
PRE_AFTER_TRADING = Event(EVENT.PRE_AFTER_TRADING)
POST_AFTER_TRADING = Event(EVENT.POST_AFTER_TRADING)
PRE_SETTLEMENT = Event(EVENT.PRE_SETTLEMENT)
POST_SETTLEMENT = Event(EVENT.POST_SETTLEMENT)


class Executor(object):
    def __init__(self, env):
        self._env = env
        self._last_before_trading = None

    def get_state(self):
        return convert_dict_to_json({"last_before_trading": self._last_before_trading}).encode('utf-8')

    def set_state(self, state):
        self._last_before_trading = convert_json_to_dict(state.decode('utf-8')).get("last_before_trading")

    def run(self, bar_dict):

        def update_time(e):
            self._env.calendar_dt = e.calendar_dt
            self._env.trading_dt = e.trading_dt

        def publish_settlement():
            event_bus.publish_event(PRE_SETTLEMENT)
            event_bus.publish_event(Event(EVENT.SETTLEMENT))
            event_bus.publish_event(POST_SETTLEMENT)

        def check_before_trading(e):
            if self._last_before_trading == event.trading_dt.date():
                return False

            if self._env.config.extra.is_hold:
                return False

            if self._last_before_trading:
                # don't publish settlement on first day
                publish_settlement()

            self._last_before_trading = e.trading_dt.date()
            update_time(e)
            event_bus.publish_event(PRE_BEFORE_TRADING)
            event_bus.publish_event(Event(EVENT.BEFORE_TRADING, calendar_dt=e.calendar_dt, trading_dt=e.trading_dt))
            event_bus.publish_event(POST_BEFORE_TRADING)

            return True

        PRE_BAR.bar_dict = bar_dict
        POST_BAR.bar_dict = bar_dict

        start_date = self._env.config.base.start_date
        end_date = self._env.config.base.end_date
        frequency = self._env.config.base.frequency
        event_bus = self._env.event_bus

        for event in self._env.event_source.events(start_date, end_date, frequency):
            if event.event_type == EVENT.TICK:
                if check_before_trading(event):
                    continue
                update_time(event)
                event_bus.publish_event(PRE_TICK)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_TICK)

            elif event.event_type == EVENT.BAR:
                if check_before_trading(event):
                    continue
                update_time(event)

                bar_dict.update_dt(event.calendar_dt)
                event_bus.publish_event(PRE_BAR)
                event.bar_dict = bar_dict
                event_bus.publish_event(event)
                event_bus.publish_event(POST_BAR)

            elif event.event_type == EVENT.BEFORE_TRADING:
                check_before_trading(event)

            elif event.event_type == EVENT.AFTER_TRADING:
                update_time(event)
                event_bus.publish_event(PRE_AFTER_TRADING)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_AFTER_TRADING)

            else:
                event_bus.publish_event(event)

        # publish settlement after last day
        publish_settlement()
