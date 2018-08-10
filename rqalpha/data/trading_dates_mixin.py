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
from rqalpha.const import MARKET


def _to_timestamp(d):
    return pd.Timestamp(d).replace(hour=0, minute=0, second=0, microsecond=0)


class TradingDatesMixin(object):
    def __init__(self, data_source):
        self._data_source = data_source

    @lru_cache(128)
    def _get_trading_dates(self, market):
        return self._data_source.get_trading_calendar(market)

    def get_trading_dates(self, start_date, end_date, market=MARKET.CN):
        # 只需要date部分
        trading_dates = self._get_trading_dates(market)

        start_date = _to_timestamp(start_date)
        end_date = _to_timestamp(end_date)
        left = trading_dates.searchsorted(start_date)
        right = trading_dates.searchsorted(end_date, side='right')
        return trading_dates[left:right]

    def get_previous_trading_date(self, date, n=1, market=MARKET.CN):
        trading_dates = self._get_trading_dates(market)

        date = _to_timestamp(date)
        pos = trading_dates.searchsorted(date)
        if pos >= n:
            return trading_dates[pos - n]
        else:
            return trading_dates[0]

    def get_next_trading_date(self, date, n=1, market=MARKET.CN):
        trading_dates = self._get_trading_dates(market)

        date = _to_timestamp(date)
        pos = trading_dates.searchsorted(date, side='right')
        if pos + n > len(trading_dates):
            return trading_dates[-1]
        else:
            return trading_dates[pos + n - 1]

    def is_trading_date(self, date, market=MARKET.CN):
        trading_dates = self._get_trading_dates(market)

        date = _to_timestamp(date)
        pos = trading_dates.searchsorted(date)
        return pos < len(trading_dates) and trading_dates[pos] == date

    @lru_cache(512)
    def _get_future_trading_date(self, dt, market):
        trading_dates = self._get_trading_dates(market)

        dt1 = dt - datetime.timedelta(hours=4)
        td = pd.Timestamp(dt1.date())
        pos = trading_dates.searchsorted(td)
        if trading_dates[pos] != td:
            raise RuntimeError('invalid future calendar datetime: {}'.format(dt))
        if dt1.hour >= 16:
            return trading_dates[pos + 1]

        return td

    def get_trading_dt(self, calendar_dt, market=MARKET.CN):
        trading_date = self.get_future_trading_date(calendar_dt, market)
        return datetime.datetime.combine(trading_date, calendar_dt.time())

    def get_future_trading_date(self, dt, market=MARKET.CN):
        return self._get_future_trading_date(dt.replace(minute=0, second=0, microsecond=0), market)

    get_nth_previous_trading_date = get_previous_trading_date

    def get_n_trading_dates_until(self, dt, n, market=MARKET.CN):
        trading_dates = self._get_trading_dates(market)

        date = _to_timestamp(dt)
        pos = trading_dates.searchsorted(date, side='right')
        if pos >= n:
            return trading_dates[pos - n:pos]

        return trading_dates[:pos]
