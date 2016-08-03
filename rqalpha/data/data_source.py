# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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

import numpy as np
import six
import pandas as pd
from collections import defaultdict
from functools import partial

from ..instruments import Instrument


class LocalDataSource(object):
    DAILY = 'daily.bcolz'
    INSTRUMENTS = 'instruments.pk'
    DIVIDEND = 'dividend.bcolz'
    TRADING_DATES = 'trading_dates.bcolz'
    YIELD_CURVE = 'yield_curve.bcolz'

    YIELD_CURVE_TENORS = {
        0: 'S0',
        30: 'M1',
        60: 'M2',
        90: 'M3',
        180: 'M6',
        270: 'M9',
        365: 'Y1',
        365 * 2: 'Y2',
        365 * 3: 'Y3',
        365 * 4: 'Y4',
        365 * 5: 'Y5',
        365 * 6: 'Y6',
        365 * 7: 'Y7',
        365 * 8: 'Y8',
        365 * 9: 'Y9',
        365 * 10: 'Y10',
        365 * 15: 'Y15',
        365 * 20: 'Y20',
        365 * 30: 'Y30',
        365 * 40: 'Y40',
        365 * 50: 'Y50',
    }

    YIELD_CURVE_DURATION = sorted(YIELD_CURVE_TENORS.keys())

    PRICE_SCALE = 1000.

    def __init__(self, root_dir):
        self._root_dir = root_dir
        import bcolz
        bcolz.defaults.out_flavor = "numpy"

        import os
        import pickle
        self._daily_table = bcolz.open(os.path.join(root_dir, LocalDataSource.DAILY))
        self._instruments = {d['order_book_id']: Instrument(d)
                             for d in pickle.load(open(os.path.join(root_dir, LocalDataSource.INSTRUMENTS), 'rb'))}
        self._dividend = bcolz.open(os.path.join(root_dir, LocalDataSource.DIVIDEND))
        self._yield_curve = bcolz.open(os.path.join(root_dir, LocalDataSource.YIELD_CURVE))
        self._trading_dates = pd.Index(pd.Timestamp(str(d)) for d in
                                       bcolz.open(os.path.join(root_dir, LocalDataSource.TRADING_DATES)))

    def instruments(self, order_book_ids):
        if isinstance(order_book_ids, six.string_types):
            try:
                return self._instruments[order_book_ids]
            except KeyError:
                print('ERROR: order_book_id {} not exists!'.format(order_book_ids))
                return None

        return [self._instruments[ob] for ob in order_book_ids
                if ob in self._instruments]

    def all_instruments(self, itype='CS'):
        if itype is None:
            return pd.DataFrame([[v.order_book_id, v.symbol, v.abbrev_symbol, v.type]
                                 for v in self._instruments.values()],
                                columns=['order_book_id', 'symbol', 'abbrev_symbol', 'type'])

        if itype not in ['CS', 'ETF', 'LOF', 'FenjiA', 'FenjiB', 'FenjiMu', 'INDX', 'Future']:
            raise ValueError('Unknown type {}'.format(itype))

        return pd.DataFrame([v.__dict__ for v in self._instruments.values() if v.type == itype])

    def sector(self, code):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and v.sector_code == code]

    def industry(self, code):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and v.industry_code == code]

    def concept(self, *concepts):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and any(c in v.concept_names.split('|') for c in concepts)]

    def get_trading_dates(self, start_date, end_date):
        left = self._trading_dates.searchsorted(start_date)
        right = self._trading_dates.searchsorted(end_date, side='right')
        return self._trading_dates[left:right]

    def get_yield_curve(self, start_date, end_date):
        duration = (end_date - start_date).days
        tenor = 0
        for t in LocalDataSource.YIELD_CURVE_DURATION:
            if duration >= t:
                tenor = t
            else:
                break

        d = start_date.year * 10000 + start_date.month * 100 + start_date.day
        return self._yield_curve.fetchwhere('date<={}'.format(d))[self.YIELD_CURVE_TENORS[tenor]][-1] / 10000.0

    def get_dividends(self, order_book_id):
        try:
            sid = self._dividend.attrs['stock_id'][order_book_id]
        except KeyError:
            return pd.DataFrame()

        try:
            dividends = self._dividend.fetchwhere('id=={}'.format(sid))
        except StopIteration:
            dividends = defaultdict(partial(np.zeros, 0))
        return pd.DataFrame({
            'book_closure_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['closure_date']),
            'ex_dividend_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['ex_date']),
            'payable_date': pd.Index(pd.Timestamp(str(d)) for d in dividends['payable_date']),
            'dividend_cash_before_tax': dividends['cash_before_tax'] / 10000.0,
            'round_lot': dividends['round_lot']
        }, index=pd.Index(pd.Timestamp(str(d)) for d in dividends['announcement_date']))

    def get_all_bars(self, order_book_id):
        try:
            # sid = self._daily_table.attrs['id_map'][order_book_id]
            start, end = self._daily_table.attrs["line_map"][order_book_id]
        except KeyError:
            raise RuntimeError('No data for {}'.format(order_book_id))

        # bars = self._daily_table.fetchwhere('id=={}'.format(sid))
        bars = self._daily_table[start:end]

        bars = bars[["date", "open", "high", "low", "close", "volume"]]
        bars = bars.astype([
                ('date', 'uint64'), ('open', 'float64'),
                ('high', 'float64'), ('low', 'float64'),
                ('close', 'float64'), ('volume', 'float64'),
            ])

        date_col = bars["date"]
        date_col[:] = 1000000 * date_col
        for key in ["open", "high", "low", "close"]:
            col = bars[key]
            col[:] = np.round(1 / self.PRICE_SCALE * col, 2)

        return bars
