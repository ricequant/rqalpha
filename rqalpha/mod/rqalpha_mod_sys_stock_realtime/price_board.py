#!/usr/bin/env python
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

from rqalpha.interface import AbstractPriceBoard
from rqalpha.utils.logger import system_log


class StockRealtimePriceBoard(AbstractPriceBoard):
    def __init__(self, realtime_quotes_df=None):
        self.realtime_quotes_df = realtime_quotes_df

    def get_last_price(self, order_book_id):
        return self.realtime_quotes_df.loc[order_book_id]['last']

    def get_limit_up(self, order_book_id):
        series = self.realtime_quotes_df.loc[order_book_id]
        rate = 1.1
        if "ST" in series["name"]:
            rate = 1.05
        return series["prev_close"] * rate

    def get_limit_down(self, order_book_id):
        return tick_snapshot['limit_down']

    def get_a1(self):
        pass

    def get_b1(self):
        pass
