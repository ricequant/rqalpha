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

from collections import namedtuple
try:
    # For Python 2 兼容
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache
import datetime


TimeRange = namedtuple('TimeRange', ['start', 'end'])


def get_month_begin_time(time=None):
    if time is None:
        time = datetime.datetime.now()
    return time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_month_end_time(time=None):
    try:
        return time.replace(month=time.month + 1, day=1, hour=23, minute=59, second=59,
                            microsecond=999) - datetime.timedelta(days=1)
    except ValueError:
        return time.replace(year=time.year + 1, month=1, day=1, hour=23, minute=59, second=59,
                            microsecond=999) - datetime.timedelta(days=1)


def get_last_date(trading_calendar, dt):
    idx = trading_calendar.searchsorted(dt)
    return trading_calendar[idx - 1]


def convert_date_to_int(dt):
    t = dt.year * 10000 + dt.month * 100 + dt.day
    t *= 1000000
    return t


def convert_dt_to_int(dt):
    t = convert_date_to_int(dt)
    t += dt.hour * 10000 + dt.minute * 100 + dt.second
    return t


def convert_int_to_date(dt_int):
    dt_int = int(dt_int)
    if dt_int > 100000000:
        dt_int //= 1000000
    return _convert_int_to_date(dt_int)


@lru_cache(None)
def _convert_int_to_date(dt_int):
    year, r = divmod(dt_int, 10000)
    month, day = divmod(r, 100)
    return datetime.datetime(year, month, day)


@lru_cache(20480)
def convert_int_to_datetime(dt_int):
    dt_int = int(dt_int)
    year, r = divmod(dt_int, 10000000000)
    month, r = divmod(r, 100000000)
    day, r = divmod(r, 1000000)
    hour, r = divmod(r, 10000)
    minute, second = divmod(r, 100)
    return datetime.datetime(year, month, day, hour, minute, second)

