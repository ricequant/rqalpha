#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Hua Liang[Stupid ET] <et@everet.org>
#

import time
import datetime
try:
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from tushare.util import dateu

from rqalpha.environment import Environment


def is_holiday_today():
    today = datetime.date.today()
    Environment.get_instance().data_proxy.get_trading_dates(today, today)


def is_tradetime_now():
    now_time = time.localtime()
    now = (now_time.tm_hour, now_time.tm_min, now_time.tm_sec)
    if (9, 15, 0) <= now <= (11, 30, 0) or (13, 0, 0) <= now <= (15, 0, 0):
        return True
    return False
