# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


from .const import EVENT_TYPE


class SimulatorAStockTradingEventSource(object):
    def __init__(self, trading_param):
        self.trading_param = trading_param
        self.timezone = trading_param.timezone
        self.generator = self.create_generator()

    def create_generator(self):
        for date in self.trading_param.trading_calendar:
            yield date.replace(hour=9, minute=0), EVENT_TYPE.DAY_START
            yield date.replace(hour=15, minute=0), EVENT_TYPE.HANDLE_BAR
            yield date.replace(hour=16, minute=0), EVENT_TYPE.DAY_END

    def __iter__(self):
        return self

    def __next__(self):
        for date, event in self.generator:
            return date, event

        raise StopIteration

    next = __next__  # Python 2
