#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Hua Liang[Stupid ET] <et@everet.org>
#

import math
import time
import datetime
try:
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

import tushare as ts
from tushare.util import dateu
from six.moves import reduce

from rqalpha.environment import Environment


def code_convert(order_book_id):
    return order_book_id.split(".")[0]


def is_holiday_today():
    today = datetime.date.today()
    Environment.get_instance().data_proxy.get_trading_dates(today, today)


def is_tradetime_now():
    now_time = time.localtime()
    now = (now_time.tm_hour, now_time.tm_min, now_time.tm_sec)
    if (9, 15, 0) <= now <= (11, 30, 0) or (13, 0, 0) <= now <= (15, 0, 0):
        return True
    return False


def get_realtime_quotes(code_list, open_only=False):
    max_len = 800
    loop_cnt = int(math.ceil(float(len(code_list)) / max_len))

    total_df = reduce(lambda df1, df2: df1.append(df2),
                      [ts.get_realtime_quotes([code for code in code_list[i::loop_cnt]])
                       for i in range(loop_cnt)])
    total_df["is_index"] = False

    index_symbol = ["sh", "sz", "hs300", "sz50", "zxb", "cyb"]
    index_df = ts.get_realtime_quotes(index_symbol)
    index_df["code"] = index_symbol
    index_df["is_index"] = True
    total_df = total_df.append(index_df)
    total_df = total_df.set_index("code").sort_index()

    columns = set(total_df.columns) - set(["name", "time", "date"])
    # columns = filter(lambda x: "_v" not in x, columns)
    for label in columns:
        total_df[label] = total_df[label].map(lambda x: 0 if str(x).strip() == "" else x)
        total_df[label] = total_df[label].astype(float)

    total_df["chg"] = total_df["price"] / total_df["pre_close"] - 1

    total_df = total_df.reset_index()

    if open_only:
        total_df = total_df[total_df.open > 0]

    return total_df
