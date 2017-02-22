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

import pandas as pd
import datetime
try:
    # For Python 2 兼容
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from ..utils import cache_control


class TradingDatesMixin(object):
    def __init__(self, dates):
        self._dates = dates

    def get_trading_dates(self, start_date, end_date):
        # 只需要date部分
        start_date = pd.Timestamp(start_date).replace(hour=0, minute=0, second=0)
        end_date = pd.Timestamp(end_date).replace(hour=0, minute=0, second=0)
        left = self._dates.searchsorted(start_date)
        right = self._dates.searchsorted(end_date, side='right')
        return self._dates[left:right]

    def get_previous_trading_date(self, date):
        date = pd.Timestamp(date).replace(hour=0, minute=0, second=0)
        return self._get_previous_trading_date(date)

    @lru_cache(cache_control.get_entry_count(128))
    def _get_previous_trading_date(self, date):
        pos = self._dates.searchsorted(date)
        if pos > 0:
            return self._dates[pos - 1]
        else:
            return self._dates[0]

    def get_next_trading_date(self, date):
        date = pd.Timestamp(date).replace(hour=0, minute=0, second=0)
        pos = self._dates.searchsorted(date, side='right')
        return self._dates[pos]

    @lru_cache(cache_control.get_entry_count(512))
    def _get_future_trading_date(self, dt):
        dt1 = dt - datetime.timedelta(hours=4)
        td = pd.Timestamp(dt1.date())
        pos = self._dates.searchsorted(td)
        if self._dates[pos] != td:
            raise RuntimeError('invalid future calendar datetime: {}'.format(dt))
        if dt1.hour >= 16:
            return self._dates[pos + 1]

        return td

    def get_trading_dt(self, calendar_dt):
        trading_date = self.get_future_trading_date(calendar_dt)
        return datetime.datetime.combine(trading_date, calendar_dt.time())

    def get_future_trading_date(self, dt):
        return self._get_future_trading_date(dt.replace(minute=0, second=0))

    def get_nth_previous_trading_date(self, date, n):
        date = pd.Timestamp(date).replace(hour=0, minute=0, second=0)
        pos = self._dates.searchsorted(date)
        if pos >= n:
            return self._dates[pos - n]
        else:
            return self._dates[0]
