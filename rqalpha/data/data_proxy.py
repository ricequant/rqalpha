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
try:
    # For Python 2 兼容
    from functools import lru_cache
except Exception as e:
    from fastcache import lru_cache

from . import risk_free_helper
from .instrument_mixin import InstrumentMixin
from .trading_dates_mixin import TradingDatesMixin
from ..model.bar import BarObject
from ..model.snapshot import SnapshotObject
from ..utils.datetime_func import convert_int_to_datetime
from ..utils import cache_control


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

    @lru_cache(cache_control.get_entry_count(128))
    def get_dividend(self, order_book_id, adjusted=True):
        return self._data_source.get_dividend(order_book_id, adjusted)

    def get_dividend_by_book_date(self, order_book_id, date, adjusted=True):
        df = self.get_dividend(order_book_id, adjusted)
        if df is None or df.empty:
            return

        dt = np.datetime64(date)
        dates = df['book_closure_date'].values
        pos = dates.searchsorted(dt)
        if pos == len(dates) or dt != dates[pos]:
            return None

        return df.iloc[pos]

    @lru_cache(cache_control.get_entry_count(10240))
    def _get_prev_close(self, order_book_id, dt):
        prev_trading_date = self.get_previous_trading_date(dt)
        instrument = self.instruments(order_book_id)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'close', prev_trading_date, False)
        if bar is None or len(bar) == 0:
            return np.nan
        return bar[0]

    def get_prev_close(self, order_book_id, dt):
        return self._get_prev_close(order_book_id, dt.replace(hour=0, minute=0, second=0))

    @lru_cache(cache_control.get_entry_count(10240))
    def _get_prev_settlement(self, instrument, dt):
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'settlement', prev_trading_date, False)
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
                                 ['datetime', field], dt, skip_suspended=False)
        if data is None:
            return None
        return pd.Series(data[field], index=[convert_int_to_datetime(t) for t in data['datetime']])

    def fast_history(self, order_book_id, bar_count, frequency, field, dt):
        return self.history_bars(order_book_id, bar_count, frequency, field, dt, skip_suspended=False)

    def history_bars(self, order_book_id, bar_count, frequency, field, dt, skip_suspended=True):
        instrument = self.instruments(order_book_id)
        return self._data_source.history_bars(instrument, bar_count, frequency, field, dt, skip_suspended)

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
