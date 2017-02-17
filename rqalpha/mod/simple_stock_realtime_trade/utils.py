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

import math
import time
import datetime
try:
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from six.moves import reduce

from rqalpha.environment import Environment
from rqalpha.utils.datetime_func import convert_dt_to_int


def is_holiday_today():
    today = datetime.date.today()
    df = Environment.get_instance().data_proxy.get_trading_dates(today, today)

    return len(df) == 0


def is_tradetime_now():
    now_time = time.localtime()
    now = (now_time.tm_hour, now_time.tm_min, now_time.tm_sec)
    if (9, 15, 0) <= now <= (11, 30, 0) or (13, 0, 0) <= now <= (15, 0, 0):
        return True
    return False


TUSHARE_CODE_MAPPING = {
    "sh": "000001.XSHG",
    "sz": "399001.XSHE",
    "sz50": "000016.XSHG",
    "hs300": "000300.XSHG",
    "sz500": "000905.XSHG",
    "zxb": "399005.XSHE",
    "cyb": "399006.XSHE",
}


def tushare_code_2_order_book_id(code):
    try:
        return TUSHARE_CODE_MAPPING[code]
    except KeyError:
        if code.startswith("6"):
            return "{}.XSHG".format(code)
        elif code[0] in ["3", "0"]:
            return "{}.XSHE".format(code)
        else:
            raise RuntimeError("Unknown code")


def order_book_id_2_tushare_code(order_book_id):
    return order_book_id.split(".")[0]


def get_realtime_quotes(code_list, open_only=False):
    import tushare as ts

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

    total_df["order_book_id"] = total_df.index
    total_df["order_book_id"] = total_df["order_book_id"].apply(tushare_code_2_order_book_id)

    total_df["datetime"] = total_df["date"] + " " + total_df["time"]
    total_df["datetime"] = total_df["datetime"].apply(lambda x: convert_dt_to_int(datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")))

    total_df["close"] = total_df["price"]

    if open_only:
        total_df = total_df[total_df.open > 0]

    return total_df
