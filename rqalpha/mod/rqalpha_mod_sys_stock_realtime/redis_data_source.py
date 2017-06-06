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
import json

import pandas as pd

from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.environment import Environment
from rqalpha.model.snapshot import SnapshotObject


class RedisDataSource(BaseDataSource):
    def __init__(self, path, redis_uri):
        super(RedisDataSource, self).__init__(path)
        self._env = Environment.get_instance()
        import redis
        self._redis_client = redis.from_url(redis_uri)

    def _get_snapshot_dict(self, order_book_id):
        snapshot = json.loads(self._redis_client[order_book_id].decode())
        return snapshot

    def get_bar(self, instrument, dt, frequency):
        snapshot_dict = self._get_snapshot_dict(instrument.order_book_id)
        return snapshot_dict

    def current_snapshot(self, instrument, frequency, dt):
        snapshot_dict = self._get_snapshot_dict(instrument.order_book_id)
        dt = pd.Timestamp(snapshot_dict["datetime"]).to_pydatetime()
        return SnapshotObject(instrument, snapshot_dict, dt=dt)

    def available_data_range(self, frequency):
        return datetime.date(2017, 1, 1), datetime.date.max
