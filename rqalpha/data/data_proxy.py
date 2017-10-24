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
import numpy as np
import pandas as pd

from rqalpha.data import risk_free_helper
from rqalpha.data.instrument_mixin import InstrumentMixin
from rqalpha.data.trading_dates_mixin import TradingDatesMixin
from rqalpha.model.bar import BarObject
from rqalpha.model.snapshot import SnapshotObject
from rqalpha.utils.py2 import lru_cache
from rqalpha.utils.datetime_func import convert_int_to_datetime, convert_date_to_int


class DataProxy(InstrumentMixin, TradingDatesMixin):
    def __init__(self, data_source):
        self._data_source = data_source
        try:
            self.get_risk_free_rate = data_source.get_risk_free_rate
        except AttributeError:
            pass
        InstrumentMixin.__init__(self, data_source.get_all_instruments())
        TradingDatesMixin.__init__(self, data_source.get_trading_calendar())

    def __getattr__(self, item):
        return getattr(self._data_source, item)

    def get_trading_minutes_for(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        minutes = self._data_source.get_trading_minutes_for(instrument, dt)
        return [] if minutes is None else minutes

    def get_yield_curve(self, start_date, end_date, tenor=None):
        if isinstance(tenor, six.string_types):
            tenor = [tenor]
        return self._data_source.get_yield_curve(start_date, end_date, tenor)

    def get_risk_free_rate(self, start_date, end_date):
        tenor = risk_free_helper.get_tenor_for(start_date, end_date)
        yc = self._data_source.get_yield_curve(start_date, start_date, [tenor])
        if yc is None or yc.empty:
            return 0
        rate = yc.values[0, 0]
        return 0 if np.isnan(rate) else rate

    def get_dividend(self, order_book_id):
        if self.instruments(order_book_id).type == 'PublicFund':
            return self._data_source.get_dividend(order_book_id, public_fund=True)
        return self._data_source.get_dividend(order_book_id)

    def get_split(self, order_book_id):
        return self._data_source.get_split(order_book_id)

    def get_dividend_by_book_date(self, order_book_id, date):
        if self.instruments(order_book_id).type == 'PublicFund':
            table = self._data_source.get_dividend(order_book_id, public_fund=True)
        else:
            table = self._data_source.get_dividend(order_book_id)
        if table is None or len(table) == 0:
            return

        dt = date.year * 10000 + date.month * 100 + date.day
        dates = table['book_closure_date']
        pos = dates.searchsorted(dt)
        if pos == len(dates) or dt != dates[pos]:
            return None

        return table[pos]

    def get_split_by_ex_date(self, order_book_id, date):
        df = self.get_split(order_book_id)
        if df is None or len(df) == 0:
            return

        dt = convert_date_to_int(date)
        pos = df['ex_date'].searchsorted(dt)
        if pos == len(df) or df['ex_date'][pos] != dt:
            return None

        return df['split_factor'][pos]

    @lru_cache(10240)
    def _get_prev_close(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'close', prev_trading_date,
                                             skip_suspended=False, include_now=False, adjust_orig=dt)
        if bar is None or len(bar) < 1:
            return np.nan
        return bar[0]

    def get_prev_close(self, order_book_id, dt):
        return self._get_prev_close(order_book_id, dt.replace(hour=0, minute=0, second=0))

    @lru_cache(10240)
    def _get_prev_settlement(self, instrument, dt):
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'settlement', prev_trading_date,
                                             skip_suspended=False, adjust_orig=dt)
        if bar is None or len(bar) == 0:
            return np.nan
        return bar[0]

    def get_prev_settlement(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        if instrument.type != 'Future':
            return np.nan
        return self._get_prev_settlement(instrument, dt)

    def get_settle_price(self, order_book_id, date):
        instrument = self.instruments(order_book_id)
        if instrument.type != 'Future':
            return np.nan
        return self._data_source.get_settle_price(instrument, date)

    def get_bar(self, order_book_id, dt, frequency='1d'):
        instrument = self.instruments(order_book_id)
        bar = self._data_source.get_bar(instrument, dt, frequency)
        if bar:
            return BarObject(instrument, bar)

    def history(self, order_book_id, bar_count, frequency, field, dt):
        data = self.history_bars(order_book_id, bar_count, frequency,
                                 ['datetime', field], dt, skip_suspended=False, adjust_orig=dt)
        if data is None:
            return None
        return pd.Series(data[field], index=[convert_int_to_datetime(t) for t in data['datetime']])

    def fast_history(self, order_book_id, bar_count, frequency, field, dt):
        return self.history_bars(order_book_id, bar_count, frequency, field, dt, skip_suspended=False,
                                 adjust_type='pre', adjust_orig=dt)

    def history_bars(self, order_book_id, bar_count, frequency, field, dt,
                     skip_suspended=True, include_now=False,
                     adjust_type='pre', adjust_orig=None):
        instrument = self.instruments(order_book_id)
        if adjust_orig is None:
            adjust_orig = dt
        return self._data_source.history_bars(instrument, bar_count, frequency, field, dt,
                                              skip_suspended=skip_suspended, include_now=include_now,
                                              adjust_type=adjust_type, adjust_orig=adjust_orig)

    def current_snapshot(self, order_book_id, frequency, dt):
        instrument = self.instruments(order_book_id)
        if frequency == '1d':
            bar = self._data_source.get_bar(instrument, dt, '1d')
            if not bar:
                return SnapshotObject(instrument, None, dt)
            d = {k: bar[k] for k in SnapshotObject.fields_for_(instrument) if k in bar.dtype.names}
            d['last'] = bar['close']
            d['prev_close'] = self._get_prev_close(order_book_id, dt)
            return SnapshotObject(instrument, d)

        return self._data_source.current_snapshot(instrument, frequency, dt)

    def available_data_range(self, frequency):
        return self._data_source.available_data_range(frequency)

    def get_margin_info(self, order_book_id):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_margin_info(instrument)

    def get_commission_info(self, order_book_id):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_commission_info(instrument)

    def get_ticks(self, order_book_id, date):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_ticks(instrument, date)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        return self._data_source.get_merge_ticks(order_book_id_list, trading_date, last_dt)

    def is_suspended(self, order_book_id, dt, count=1):
        if count == 1:
            return self._data_source.is_suspended(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.is_suspended(order_book_id, trading_dates)

    def is_st_stock(self, order_book_id, dt, count=1):
        if count == 1:
            return self._data_source.is_st_stock(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.is_st_stock(order_book_id, trading_dates)

    def non_subscribable(self, order_book_id, dt, count=1):
        if count == 1:
            return self._data_source.non_subscribable(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.non_subscribable(order_book_id, trading_dates)

    def non_redeemable(self, order_book_id, dt, count=1):
        if count == 1:
            return self._data_source.non_redeemable(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.non_redeemable(order_book_id, trading_dates)

    def public_fund_commission(self, order_book_id, buy):
        instrument = self.instruments(order_book_id)
        return self._data_source.public_fund_commission(instrument, buy)
