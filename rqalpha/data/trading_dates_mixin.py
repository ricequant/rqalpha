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

from rqalpha.utils.py2 import lru_cache


def _to_timestamp(d):
    return pd.Timestamp(d).replace(hour=0, minute=0, second=0, microsecond=0)


class TradingDatesMixin(object):
    def __init__(self, dates):
        self._dates = dates

    def get_trading_dates(self, start_date, end_date):
        # 只需要date部分
        start_date = _to_timestamp(start_date)
        end_date = _to_timestamp(end_date)
        left = self._dates.searchsorted(start_date)
        right = self._dates.searchsorted(end_date, side='right')
        return self._dates[left:right]

    def get_previous_trading_date(self, date, n=1):
        date = _to_timestamp(date)
        pos = self._dates.searchsorted(date)
        if pos >= n:
            return self._dates[pos - n]
        else:
            return self._dates[0]

    def get_next_trading_date(self, date, n=1):
        date = _to_timestamp(date)
        pos = self._dates.searchsorted(date, side='right')
        if pos + n > len(self._dates):
            return self._dates[-1]
        else:
            return self._dates[pos + n - 1]

    def is_trading_date(self, date):
        date = _to_timestamp(date)
        pos = self._dates.searchsorted(date)
        return pos < len(self._dates) and self._dates[pos] == date

    @lru_cache(512)
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
        return self._get_future_trading_date(dt.replace(minute=0, second=0, microsecond=0))

    get_nth_previous_trading_date = get_previous_trading_date

    def get_n_trading_dates_until(self, dt, n):
        date = _to_timestamp(dt)
        pos = self._dates.searchsorted(date, side='right')
        if pos >= n:
            return self._dates[pos - n:pos]

        return self._dates[:pos]
