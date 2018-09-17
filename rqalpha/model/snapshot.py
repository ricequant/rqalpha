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

import numpy as np

from rqalpha.utils.logger import system_log
from rqalpha.model.tick import TickObject


class SnapshotObject(TickObject):
    _STOCK_FIELDS = [
        ('datetime', np.uint64),
        ('open', np.float64),
        ('high', np.float64),
        ('low', np.float64),
        ('last', np.float64),
        ('volume', np.int32),
        ('total_turnover', np.int64),
        ('prev_close', np.float64)
    ]

    _FUTURE_FIELDS = _STOCK_FIELDS + [('open_interest', np.int32), ('prev_settlement', np.float64)]

    _STOCK_FIELD_NAMES = [_n for _n, _ in _STOCK_FIELDS]
    _FUTURE_FIELD_NAMES = [_n for _n, _ in _FUTURE_FIELDS]
    _STOCK_FIELD_DTYPE = np.dtype(_STOCK_FIELDS)
    _FUTURE_FIELD_DTYPE = np.dtype(_FUTURE_FIELDS)

    _NANDict = {_n: np.nan for _n in _FUTURE_FIELD_NAMES}

    def __init__(self, instrument, data, dt=None):
        system_log.warn("[deprecated] SnapshotObject class is no longer used. use TickObject class instead.")
        if data is None:
            data = self._NANDict

        if dt:
            data["datetime"] = dt

        super(SnapshotObject, self).__init__(instrument, data)

    @staticmethod
    def dtype_for_(instrument):
        if instrument.type == 'Future':
            return SnapshotObject._FUTURE_FIELD_DTYPE
        else:
            return SnapshotObject._STOCK_FIELD_DTYPE

    @staticmethod
    def fields_for_(instrument):
        if instrument.type == 'Future':
            return SnapshotObject._FUTURE_FIELD_NAMES
        else:
            return SnapshotObject._STOCK_FIELD_NAMES
