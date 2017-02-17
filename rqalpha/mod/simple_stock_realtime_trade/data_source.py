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

import pandas as pd
import tushare as ts

from rqalpha.utils.datetime_func import convert_int_to_date
from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.environment import Environment
from rqalpha.model.snapshot import SnapshotObject
from .utils import order_book_id_2_tushare_code


class DataSource(BaseDataSource):
    def __init__(self, path):
        super(DataSource, self).__init__(path)
        self._env = Environment.get_instance()
        self.realtime_quotes_df = pd.DataFrame()

    def get_bar(self, instrument, dt, frequency):
        bar = ts.get_realtime_quotes(order_book_id_2_tushare_code(instrument.order_book_id)).iloc[0].to_dict()
        dt = int(bar["date"].replace("-", "")) * 1000000 + int(bar["time"].replace(":", ""))
        bar["datetime"] = dt

        for item in ["date", "time", "code", "name"]:
            bar.pop(item, None)

        for item in set(bar.keys()) - set(["datetime"]):
            bar[item] = float(bar[item])

        bar["close"] = bar["price"]

        return bar

    def current_snapshot(self, instrument, frequency, dt):
        snapshot_dict = self.realtime_quotes_df.loc[instrument.order_book_id].to_dict()
        snapshot_dict["last"] = snapshot_dict["price"]
        print("snapshot_dict", snapshot_dict)
        # snapshot_dict = self._redis_store.get_snapshot(instrument.order_book_id)
        return SnapshotObject(instrument, snapshot_dict)

    def available_data_range(self, frequency):
        if frequency == '1d':
            s, e = self._day_bars[self.INSTRUMENT_TYPE_MAP['INDX']].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

        if frequency == '1m':
            return datetime.date(2016, 1, 1), datetime.date(2017, 2, 15)
