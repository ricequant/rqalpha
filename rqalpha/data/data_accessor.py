# -*- coding: utf-8 -*-
import abc

from six import with_metaclass, iteritems
import pandas as pd

from .bar import BarObject
from ..utils.context import ExecutionContext
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
    def get_dividend_per_share(self, order_book_id, date):
        """get dividend of date

        :param str order_book_id:
        :param datetime.datetime date:
        :returns: dividend per share
        :rtype: float

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

    def get_bar(self, order_book_id, dt):
        if order_book_id not in self._cache:
            self._cache[order_book_id] = self._data_source.get_all_bars(order_book_id)

        pf = self._cache[order_book_id]

        return BarObject(self._data_source.instruments(order_book_id), pf.xs(dt.date()))

    def history(self, order_book_id, bar_count, frequency, field):
        if frequency == '1m':
            raise RuntimeError('Minute bar not supported yet!')

        try:
            df = self._cache[order_book_id]
        except KeyError:
            df = self._data_source.get_all_bars(order_book_id)
            self._cache[order_book_id] = df

        dt = ExecutionContext.get_current_dt().date()
        i = df.index.searchsorted(dt, side='right')
        left = i - bar_count if i >= bar_count else 0
        return df[left:i][field]

    def get_yield_curve(self, start_date=None, end_date=None):
        return self._data_source.get_yield_curve(start_date, end_date)

    def get_dividend_per_share(self, order_book_id, date):
        if order_book_id not in self._dividend_cache:
            dividend_df = self._data_source.get_dividends(order_book_id)
            if not dividend_df.empty:
                dividend_df.set_index("payable_date", inplace=True)
            self._dividend_cache[order_book_id] = dividend_df

        dividend_df = self._dividend_cache[order_book_id]
        try:
            series = dividend_df.ix[date]
        except KeyError:
            return 0

        return series["dividend_cash_before_tax"] / series["round_lot"]

    def get_trading_dates(self, start_date, end_date):
        return self._data_source.get_trading_dates(start_date, end_date)

    def instrument(self, order_book_id):
        return self._data_source.instruments(order_book_id)
