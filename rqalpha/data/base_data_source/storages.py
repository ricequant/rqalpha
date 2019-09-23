# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import codecs
import pickle
from copy import copy

import six
import json
import bcolz
import numpy as np
import pandas as pd

from rqalpha.utils.i18n import gettext as _
from rqalpha.const import COMMISSION_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils import risk_free_helper


class DayBarStore(object):
    def __init__(self, main, converter):
        self._table = bcolz.open(main, 'r')
        self._index = self._table.attrs['line_map']
        self._converter = converter

    @staticmethod
    def _remove_(l, v):
        try:
            l.remove(v)
        except ValueError:
            pass

    def get_bars(self, order_book_id, fields=None):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            six.print_(_(u"No data for {}").format(order_book_id))
            return

        if fields is None:
            # the first is date
            fields = self._table.names[1:]

        if len(fields) == 1:
            return self._converter.convert(fields[0], self._table.cols[fields[0]][s:e])

        # remove datetime if exist in fields
        self._remove_(fields, 'datetime')

        dtype = np.dtype([('datetime', np.uint64)] +
                         [(f, self._converter.field_type(f, self._table.cols[f].dtype))
                          for f in fields])
        result = np.empty(shape=(e - s, ), dtype=dtype)
        for f in fields:
            result[f] = self._converter.convert(f, self._table.cols[f][s:e])
        result['datetime'] = self._table.cols['date'][s:e]
        result['datetime'] *= 1000000

        return result

    def get_date_range(self, order_book_id):
        s, e = self._index[order_book_id]
        return self._table.cols['date'][s], self._table.cols['date'][e - 1]


class DividendStore(object):
    def __init__(self, f):
        ct = bcolz.open(f, 'r')
        self._index = ct.attrs['line_map']
        self._table = np.empty((len(ct), ), dtype=np.dtype([
            ('announcement_date', '<u4'), ('book_closure_date', '<u4'),
            ('ex_dividend_date', '<u4'), ('payable_date', '<u4'),
            ('dividend_cash_before_tax', np.float), ('round_lot', '<u4')
        ]))
        self._table['announcement_date'][:] = ct['announcement_date']
        self._table['book_closure_date'][:] = ct['closure_date']
        self._table['ex_dividend_date'][:] = ct['ex_date']
        self._table['payable_date'][:] = ct['payable_date']
        self._table['dividend_cash_before_tax'] = ct['cash_before_tax'][:] / 10000.0
        self._table['round_lot'][:] = ct['round_lot']

    def get_dividend(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return None

        return self._table[s:e]


class FutureInfoStore(object):
    COMMISSION_TYPE_MAP = {
        "by_volume": COMMISSION_TYPE.BY_VOLUME,
        "by_money": COMMISSION_TYPE.BY_MONEY
    }

    def __init__(self, f, custom_future_info):
        with open(f, "r") as json_file:
            self._default_data = {
                item.get("order_book_id") or item.get("underlying_symbol"): self._process_future_info_item(
                    item
                ) for item in json.load(json_file)
            }
        self._custom_data = custom_future_info
        self._future_info = {}

    @classmethod
    def _process_future_info_item(cls, item):
        item["commission_type"] = cls.COMMISSION_TYPE_MAP[item["commission_type"]]
        return item

    def get_future_info(self, instrument):
        order_book_id = instrument.order_book_id
        try:
            return self._future_info[order_book_id]
        except KeyError:
            custom_info = self._custom_data.get(order_book_id) or self._custom_data.get(instrument.underlying_symbol)
            info = self._default_data.get(order_book_id) or self._default_data.get(instrument.underlying_symbol)
            if custom_info:
                info = copy(info) or {}
                info.update(custom_info)
            elif not info:
                raise NotImplementedError(_("unsupported future instrument {}").format(order_book_id))
            return self._future_info.setdefault(order_book_id, info)


class InstrumentStore(object):
    def __init__(self, f):
        with open(f, 'rb') as store:
            d = pickle.load(store)
        self._instruments = [Instrument(i) for i in d]

    def get_all_instruments(self):
        return self._instruments


class ShareTransformationStore(object):
    def __init__(self, f):
        with codecs.open(f, 'r', encoding="utf-8") as store:
            self._share_transformation = json.load(store)

    def get_share_transformation(self, order_book_id):
        try:
            transformation_data = self._share_transformation[order_book_id]
        except KeyError:
            return
        return transformation_data["successor"], transformation_data["share_conversion_ratio"]


class SimpleFactorStore(object):
    def __init__(self, f):
        table = bcolz.open(f, 'r')
        self._index = table.attrs['line_map']
        self._table = table[:]

    def get_factors(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
            return self._table[s:e]
        except KeyError:
            return None


class TradingDatesStore(object):
    def __init__(self, f):
        self._dates = pd.Index(pd.Timestamp(str(d)) for d in bcolz.open(f, 'r'))

    def get_trading_calendar(self):
        return self._dates


class YieldCurveStore(object):
    def __init__(self, f):
        self._table = bcolz.open(f, 'r')
        self._dates = self._table.cols['date'][:]

    def get_yield_curve(self, start_date, end_date, tenor):
        d1 = start_date.year * 10000 + start_date.month * 100 + start_date.day
        d2 = end_date.year * 10000 + end_date.month * 100 + end_date.day

        s = self._dates.searchsorted(d1)
        e = self._dates.searchsorted(d2, side='right')

        if e == len(self._dates):
            e -= 1
        if self._dates[e] == d2:
            # 包含 end_date
            e += 1

        if e < s:
            return None

        df = pd.DataFrame(self._table[s:e])
        df.index = pd.Index(pd.Timestamp(str(d)) for d in df['date'])
        del df['date']

        df.rename(columns=lambda n: n[1:]+n[0], inplace=True)
        if tenor is not None:
            return df[tenor]
        return df

    def get_risk_free_rate(self, start_date, end_date):
        tenor = risk_free_helper.get_tenor_for(start_date, end_date)
        tenor = tenor[-1] + tenor[:-1]
        d = start_date.year * 10000 + start_date.month * 100 + start_date.day
        pos = self._dates.searchsorted(d)
        if pos > 0 and (pos == len(self._dates) or self._dates[pos] != d):
            pos -= 1

        col = self._table.cols[tenor]
        while pos >= 0 and np.isnan(col[pos]):
            # data is missing ...
            pos -= 1

        return self._table.cols[tenor][pos]
