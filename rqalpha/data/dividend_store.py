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
import pandas as pd
try:
    # For Python 2 兼容
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from ..utils import cache_control


class DividendStore(object):
    def __init__(self, f):
        self._table = bcolz.open(f, 'r')
        self._index = self._table.attrs['line_map']

    @lru_cache(cache_control.get_entry_count(128))
    def get_dividend(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return pd.DataFrame()

        dividends = self._table[s:e]
        return pd.DataFrame({
            'book_closure_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['closure_date']),
            'ex_dividend_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['ex_date']),
            'payable_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['payable_date']),
            'dividend_cash_before_tax': dividends['cash_before_tax'] / 10000.0,
            'round_lot': dividends['round_lot']
        }, index=pd.Index(pd.Timestamp(str(d)) for d in dividends['announcement_date']))
