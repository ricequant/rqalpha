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

from __future__ import division

import abc
import datetime
import pandas as pd
import numpy as np
from six import with_metaclass, string_types

from .bar import BarObject
from ..utils.context import ExecutionContext
from ..utils import convert_date_to_int, convert_int_to_date
from .data_source import LocalDataSource


class DataProxy(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_bar(self, order_book_id, dt):
        """get stock Bar object

        :param str order_book_id:
        :param datetime.datetime dt:
        :returns: bar object
        :rtype: BarObject

        """
        raise NotImplementedError

    def latest_bar(self, order_book_id):
        """get latest bar of the stock

        :param str order_book_id:
        :returns: bar object
        :rtype: BarObject

        """
        dt = ExecutionContext.get_current_dt()

        return self.get_bar(order_book_id, dt)

    @abc.abstractmethod
    def get_yield_curve(self, start_date=None, end_date=None):
        """get yield curve of treasure

        :param datetime.date start_date:
        :param datetime.date end_date:
        :returns:
        :rtype: pd.DataFrame

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_dividends_by_book_date(self, order_book_id, date):
        """get dividend of info by ex date

        :param str order_book_id:
        :param datetime.datetime date:
        :returns: dividend
        :rtype: pd.Series

        """
        raise NotImplementedError

    @abc.abstractmethod
    def history(self, order_book_id, dt, bar_count, frequency, field):
        """get history data

        :param str order_book_id:
        :param datetime dt:
        :param int bar_count:
        :param str frequency: '1d' or '1m'
        :param str field: "open", "close", "high", "low", "volume", "last", "total_turnover"
        :returns:
        :rtype: pandas.DataFrame

        """
        raise NotImplementedError

    def last(self, order_book_id, dt, bar_count, frequency, field):
        """get history data, will not fill empty data

        :param str order_book_id:
        :param datetime dt:
        :param int bar_count:
        :param str frequency: '1d' or '1m'
        :param str field: "open", "close", "high", "low", "volume", "last", "total_turnover"
        :returns:
        :rtype: pandas.DataFrame

        """
        raise NotImplementedError

    @abc.abstractmethod
    def instrument(self, order_book_id):
        """get instrument of order book id

        :param str order_book_id:
        :returns: result instrument
        :rtype: Instrument

        """
        raise NotImplementedError


class LocalDataProxy(DataProxy):

    def __init__(self, root_dir):
        self._data_source = LocalDataSource(root_dir)
        self._cache = {}
        self._origin_cache = {}
        self._dividend_cache = {}

        self.trading_calendar = self.get_trading_dates("2005-01-01", datetime.date.today())
        trading_calender_int = np.array(
            [int(t.strftime("%Y%m%d000000")) for t in self.trading_calendar], dtype="<u8")
        self.trading_calender_int = trading_calender_int[
            trading_calender_int <= convert_date_to_int(datetime.date.today())]

    def get_bar(self, order_book_id, dt):
        try:
            bars = self._cache[order_book_id]
        except KeyError:
            bars = self._data_source.get_all_bars(order_book_id)
            bars = self._fill_all_bars(bars)
            self._cache[order_book_id] = bars

        if isinstance(dt, string_types):
            dt = pd.Timestamp(dt)

        instrument = self._data_source.instruments(order_book_id)
        # dt = int(pd.Timestamp(dt).strftime("%Y%m%d%H%M%S"))
        dt = convert_date_to_int(dt)
        return BarObject(instrument, bars[bars["date"].searchsorted(dt)])

    def history(self, order_book_id, dt, bar_count, frequency, field):
        if frequency == '1m':
            raise RuntimeError('Minute bar not supported yet!')

        try:
            bars = self._cache[order_book_id]
        except KeyError:
            bars = self._data_source.get_all_bars(order_book_id)
            bars = self._fill_all_bars(bars)
            self._cache[order_book_id] = bars

        dt = convert_date_to_int(dt)

        i = bars["date"].searchsorted(dt)
        left = i - bar_count + 1 if i >= bar_count else 0
        bars = bars[left:i + 1]

        series = pd.Series(bars[field], index=[convert_int_to_date(t) for t in bars["date"]])

        return series

    def last(self, order_book_id, dt, bar_count, frequency, field):
        if frequency == '1m':
            raise RuntimeError('Minute bar not supported yet!')

        try:
            bars = self._origin_cache[order_book_id]
        except KeyError:
            bars = self._data_source.get_all_bars(order_book_id)
            bars = bars[bars["volume"] > 0]
            self._origin_cache[order_book_id] = bars

        dt = convert_date_to_int(dt)

        i = bars["date"].searchsorted(dt)
        left = i - bar_count + 1 if i >= bar_count else 0
        hist = bars[left:i + 1][field]

        return hist

    def get_yield_curve(self, start_date=None, end_date=None):
        return self._data_source.get_yield_curve(start_date, end_date)

    def get_dividends_by_book_date(self, order_book_id, date):
        if order_book_id not in self._dividend_cache:
            dividend_df = self._data_source.get_dividends(order_book_id)
            if not dividend_df.empty:
                dividend_df.set_index("book_closure_date", inplace=True)
            self._dividend_cache[order_book_id] = dividend_df

        dividend_df = self._dividend_cache[order_book_id]
        try:
            series = dividend_df.ix[date]
            return series
        except KeyError:
            return None

    def get_trading_dates(self, start_date, end_date):
        return self._data_source.get_trading_dates(start_date, end_date)

    def instrument(self, order_book_id):
        return self._data_source.instruments(order_book_id)

    def _fill_all_bars(self, bars):
        trading_calender_int = self.trading_calender_int

        # prepend
        prepend_date = trading_calender_int[:trading_calender_int.searchsorted(bars[0]["date"])]
        prepend_bars = np.zeros(len(prepend_date), dtype=bars.dtype)
        dates = prepend_bars["date"]
        dates[:] = prepend_date

        # append
        append_date = trading_calender_int[trading_calender_int.searchsorted(bars[-1]["date"]) + 1:]
        append_bars = np.zeros(len(append_date), dtype=bars.dtype)
        dates = append_bars["date"]
        dates[:] = append_date

        for key in ["open", "high", "low", "close"]:
            col = append_bars[key]
            col[:] = bars[-1][key]  # fill with bars's last bar

        # fill bars
        new_bars = np.concatenate([prepend_bars, bars, append_bars])
        return new_bars
