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

import bcolz
import numpy as np
try:
    # For Python 2 兼容
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from ..utils import cache_control


class DateSet(object):
    def __init__(self, f):
        self._dates = bcolz.open(f, 'r')
        self._index = self._dates.attrs['line_map']

    @lru_cache(cache_control.get_entry_count(None))
    def _get_set(self, s, e):
        return set(self._dates[s:e])

    def get_days(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return []

        return self._get_set(s, e)

    def contains(self, order_book_id, dt):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return False

        if isinstance(dt, (int, np.int64, np.uint64)):
            if dt > 100000000:
                dt //= 1000000
        else:
            dt = dt.year*10000 + dt.month*100 + dt.day

        return dt in self._get_set(s, e)
