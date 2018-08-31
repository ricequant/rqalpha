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

import six
import bcolz
import numpy as np
from pandas import DataFrame

from rqalpha.environment import Environment
from rqalpha.data.daybar_store import DayBarStore
from rqalpha.data.risk_free_helper import YIELD_CURVE_TENORS
from rqalpha.utils.datetime_func import convert_int_to_date


class HkYieldCurveMocker(object):
    def __init__(self):
        self._env = Environment.get_instance()
        self._tenors = list(six.itervalues(YIELD_CURVE_TENORS))

    def get_yield_curve(self, start_date, end_date, tenor):
        dates = self._env.data_proxy.get_trading_dates(start_date, end_date)

        if tenor is None:
            tenor = self._tenors

        if isinstance(tenor, six.string_types):
            tenor = [tenor]

        for t in tenor:
            if t not in self._tenors:
                raise KeyError("{} not in index".format(t))

        return DataFrame(index=dates, data={
            t: [0.02] * len(dates) for t in tenor
        })

    @staticmethod
    def get_risk_free_rate(*_, **__):
        return 0.02


class HkDividendStore(object):
    def __init__(self, f):
        ct = bcolz.open(f, 'r')
        self._index = ct.attrs['line_map']
        self._table = np.empty((len(ct), ), dtype=np.dtype([
            ('ex_dividend_date', '<u4'), ('dividend_cash_before_tax', np.float), ('round_lot', '<u4')
        ]))

        self._table['ex_dividend_date'][:] = ct['ex_date']
        self._table['dividend_cash_before_tax'] = ct['cash_before_tax'][:] / 10000.0
        self._table['round_lot'][:] = ct['round_lot']

    def get_dividend(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return None

        return self._table[s:e]


class HkDayBarStore(DayBarStore):
    def get_available_data_range(self):
        min_date, max_date = self._table.attrs["min_date"], self._table.attrs["max_date"]
        return convert_int_to_date(min_date).date(), convert_int_to_date(max_date).date()
