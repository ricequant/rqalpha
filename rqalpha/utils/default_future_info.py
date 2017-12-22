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

from datetime import time

from rqalpha.utils.datetime_func import TimeRange

TRADING_PERIOD_DICT = dict()

STOCK_TRADING_PERIOD = [
    TimeRange(start=time(9, 31), end=time(11, 30)),
    TimeRange(start=time(13, 1), end=time(15, 0)),
]

# | 商品期货 WR, FU, CS, C, L, V, PP, BB, FB, JD, WH, PM, RI, SF, SM, RS, JR, LR, AP  | 09:01~10:15, 10:31~11:30, 13:31~15:00 |
time_period1 = [
    TimeRange(start=time(9, 1), end=time(10, 15)),
    TimeRange(start=time(10, 31), end=time(11, 30)),
    TimeRange(start=time(13, 31), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update({
    underlying_symbol: time_period1
    for underlying_symbol in
    ["WR", "FU", "CS", "C", "L", "V", "PP", "BB", "FB", "JD", "WH", "PM", "RI", "SF", "SM", "RS", "JR", "LR", "AP"]
})

# | 商品期货 Y, M, A, B, P, J, JM, I, CF, SR, OI, TA, MA, ZC, FG, RM | 21:01~23:30, 09:01~10:15, 10:31~11:30, 13:31~15:00 |
time_period2 = [
    TimeRange(start=time(21, 1), end=time(23, 30)),
    TimeRange(start=time(9, 1), end=time(10, 15)),
    TimeRange(start=time(10, 31), end=time(11, 30)),
    TimeRange(start=time(13, 31), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update({
    underlying_symbol: time_period2
    for underlying_symbol in ["Y", "M", "A", "B", "P", "J", "JM", "I", "CF", "SR", "OI", "TA", "MA", "ZC", "FG", "RM"]
})

# | 商品期货 CU, AL, ZN, PB, SN, NI | 21:01~1:00, 09:01~10:15, 10:31~11:30, 13:31~15:00 |
time_period3 = [
    TimeRange(start=time(21, 1), end=time(23, 59)),
    TimeRange(start=time(0, 0), end=time(1, 0)),
    TimeRange(start=time(9, 1), end=time(10, 15)),
    TimeRange(start=time(10, 31), end=time(11, 30)),
    TimeRange(start=time(13, 31), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update(
    {underlying_symbol: time_period3
     for underlying_symbol in ["CU", "AL", "ZN", "PB", "SN", "NI"]})

# | 商品期货 RB, HC, BU, RU | 21:01~23:00, 09:01~10:15, 10:31~11:30, 13:31~15:00 |
time_period4 = [
    TimeRange(start=time(21, 1), end=time(23, 0)),
    TimeRange(start=time(9, 1), end=time(10, 15)),
    TimeRange(start=time(10, 31), end=time(11, 30)),
    TimeRange(start=time(13, 31), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update({underlying_symbol: time_period4 for underlying_symbol in ["RB", "HC", "BU", "RU"]})

# | 商品期货 AU, AG | 21:01~2:30, 09:01~10:15, 10:31~11:30, 13:31~15:00 |
time_period5 = [
    TimeRange(start=time(21, 1), end=time(23, 59)),
    TimeRange(start=time(0, 0), end=time(2, 30)),
    TimeRange(start=time(9, 1), end=time(10, 15)),
    TimeRange(start=time(10, 31), end=time(11, 30)),
    TimeRange(start=time(13, 31), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update({underlying_symbol: time_period5 for underlying_symbol in ["AU", "AG"]})

# | 股指期货 product='Index' | 09:31~11:30, 13:01~15:00 |
time_period6 = [
    TimeRange(start=time(9, 31), end=time(11, 30)),
    TimeRange(start=time(13, 1), end=time(15, 0)),
]
TRADING_PERIOD_DICT.update({underlying_symbol: time_period6 for underlying_symbol in ["IF", "IH", "IC"]})

# | 国债期货 product='Government' | 09:16~11:30, 13:01~15:15|
time_period7 = [
    TimeRange(start=time(9, 16), end=time(11, 30)),
    TimeRange(start=time(13, 1), end=time(15, 15)),
]
TRADING_PERIOD_DICT.update({underlying_symbol: time_period7 for underlying_symbol in ["T", "TF"]})
