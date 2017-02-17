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

import tushare as ts

from rqalpha.utils.datetime_func import convert_int_to_date
from rqalpha.data.base_data_source import BaseDataSource
from .utils import code_convert


class DataSource(BaseDataSource):

    def get_bar(self, instrument, dt, frequency):
        bar = ts.get_realtime_quotes(code_convert(instrument.order_book_id)).iloc[0].to_dict()
        dt = int(bar["date"].replace("-", "")) * 1000000 + int(bar["time"].replace(":", ""))
        bar["datetime"] = dt

        for item in ["date", "time", "code", "name"]:
            bar.pop(item, None)

        for item in set(bar.keys()) - set(["datetime"]):
            bar[item] = float(bar[item])

        bar["close"] = bar["price"]

        return bar

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    def available_data_range(self, frequency):
        if frequency == '1d':
            s, e = self._day_bars[self.INSTRUMENT_TYPE_MAP['INDX']].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

        if frequency == '1m':
            return datetime.date(2016, 1, 1), datetime.date(2017, 2, 15)
