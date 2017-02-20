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

from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.environment import Environment
from rqalpha.model.snapshot import SnapshotObject


class DataSource(BaseDataSource):
    def __init__(self, path):
        super(DataSource, self).__init__(path)
        self._env = Environment.get_instance()
        self.realtime_quotes_df = pd.DataFrame()

    def get_bar(self, instrument, dt, frequency):
        # if frequency == '1d':
        #     return super(DataSource, self).get_bar(instrument, dt, frequency)

        # FIXME: 目前这样仅仅给撮合引擎用，不是定义的bar
        # FIXME: self.realtime_quotes_df 是从 event_source.py 那边「飞线」设置过来的
        bar = self.realtime_quotes_df.loc[instrument.order_book_id].to_dict()

        return bar

    def current_snapshot(self, instrument, frequency, dt):
        snapshot_dict = self.realtime_quotes_df.loc[instrument.order_book_id].to_dict()
        snapshot_dict["last"] = snapshot_dict["price"]
        return SnapshotObject(instrument, snapshot_dict)

    def available_data_range(self, frequency):
        return datetime.date(2017, 1, 1), datetime.date.max
