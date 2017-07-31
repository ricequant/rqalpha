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

    KNOWN_EVENTS = {
        EVENT.TICK,
        EVENT.BAR,
        EVENT.BEFORE_TRADING,
        EVENT.AFTER_TRADING,
        EVENT.POST_SETTLEMENT,
    }

    def run(self, bar_dict):
        PRE_BAR.bar_dict = bar_dict
        POST_BAR.bar_dict = bar_dict

        start_date = self._env.config.base.start_date
        end_date = self._env.config.base.end_date
        frequency = self._env.config.base.frequency
        event_bus = self._env.event_bus

        for event in self._env.event_source.events(start_date, end_date, frequency):
            if event.event_type in self.KNOWN_EVENTS:
                self._env.calendar_dt = event.calendar_dt
                self._env.trading_dt = event.trading_dt

            if event.event_type == EVENT.TICK:
                event_bus.publish_event(PRE_TICK)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_TICK)
            elif event.event_type == EVENT.BAR:
                bar_dict.update_dt(event.calendar_dt)
                event_bus.publish_event(PRE_BAR)
                event.bar_dict = bar_dict
                event_bus.publish_event(event)
                event_bus.publish_event(POST_BAR)
            elif event.event_type == EVENT.BEFORE_TRADING:
                event_bus.publish_event(PRE_BEFORE_TRADING)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_BEFORE_TRADING)
            elif event.event_type == EVENT.AFTER_TRADING:
                event_bus.publish_event(PRE_AFTER_TRADING)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_AFTER_TRADING)
            elif event.event_type == EVENT.SETTLEMENT:
                event_bus.publish_event(PRE_SETTLEMENT)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_SETTLEMENT)
            else:
                event_bus.publish_event(event)
