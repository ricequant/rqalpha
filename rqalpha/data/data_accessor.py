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

import abc
import datetime

from six import with_metaclass, iteritems
import pandas as pd
import numpy as np

from .bar import BarObject
from ..utils.context import ExecutionContext
from .data_source import LocalDataSource
from ..const import EXECUTION_PHASE


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
    def history(self, order_book_id, bar_count, frequency, field):
        """get history data

        :param str order_book_id:
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
        self._dividend_cache = {}

        self.trading_calendar = self.get_trading_dates("2005-01-01", datetime.date.today())

    def get_bar(self, order_book_id, dt):
        try:
            df = self._cache[order_book_id]
        except KeyError:
            df = self._data_source.get_all_bars(order_book_id)
            df = self._fill_all_bars(df)
            self._cache[order_book_id] = df

        instrument = self._data_source.instruments(order_book_id)
        return BarObject(instrument, df.xs(dt.date()))

    def history(self, order_book_id, bar_count, frequency, field):
        if frequency == '1m':
            raise RuntimeError('Minute bar not supported yet!')

        try:
            df = self._cache[order_book_id]
        except KeyError:
            df = self._data_source.get_all_bars(order_book_id)
            df = self._fill_all_bars(df)
            self._cache[order_book_id] = df

        dt = ExecutionContext.get_current_dt().date()
        i = df.index.searchsorted(dt, side='right')
        # you can only access yesterday history in before_trading
        if ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
            i -= 1
        left = i - bar_count if i >= bar_count else 0
        hist = df[left:i][field]

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

    def _fill_all_bars(self, df):
        trading_calendar = self.trading_calendar

        t = df.index[0] if not df.empty else pd.Timestamp(datetime.date.today())
        _df = pd.DataFrame(columns=df.columns, index=trading_calendar[trading_calendar < t]).fillna(0)
        df = pd.concat([_df, df])

        t = df.index[-1]
        _df = pd.DataFrame(columns=df.columns, index=trading_calendar[trading_calendar > t])
        for column in df.columns:
            _df[column] = df.iloc[-1][column]
        df = pd.concat([df, _df])

        return df
