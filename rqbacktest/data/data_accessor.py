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

    @abc.abstractclassmethod
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



class RqDataProxy(DataProxy):
    fields_mapping = {
        "ClosingPx": "close",
        "OpeningPx": "open",
        "HighPx": "high",
        "LowPx": "low",
        "TotalVolumeTraded": "volume",
        "TotalTurnover": "total_turnover",
        # TODO: fill bar
    }

    def __init__(self):
        import rqdata
        self.rqdata = rqdata
        # rqdata.init()
        self.cache = {}

    def get_bar(self, order_book_id, dt):
        # should use a better cache here
        rqdata = self.rqdata

        cache_key = "get_bar:%s" % order_book_id
        data = self.cache.get(cache_key)
        if data is None:
            data = rqdata.get_price(order_book_id, start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = data

        str_date = dt.strftime("%Y-%m-%d")
        try:
            bar_data = data.ix[str_date]
        except KeyError:
            bar_data = data[data.index <= str_date].iloc[-1]

        bar = BarObject(None, bar_data)
        return bar

    def get_yield_curve(self, start_date=None, end_date=None):
        rqdata = self.rqdata

        cache_key = "get_yield_curve"
        data = self.cache.get(cache_key)
        if data is None:
            data = rqdata.get_yield_curve(start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = data
        return data

    def get_dividend_per_share(self, order_book_id, date):
        rqdata = self.rqdata

        cache_key = "get_dividend:%s" % order_book_id
        dividend_df = self.cache.get(cache_key)
        if dividend_df is None:
            dividend_df = rqdata.get_dividend(order_book_id, start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = dividend_df

        df = dividend_df[dividend_df.payable_date == date]

        if df.empty:
            return 0

        return df.iloc[0]["dividend_cash_before_tax"] / df.iloc[0]["round_lot"]

    def history(self, order_book_id, bar_count, frequency, field):
        if frequency != "1d":
            raise NotImplementedError

        rqdata = self.rqdata

        cache_key = "get_bar:%s" % order_book_id
        data = self.cache.get(cache_key)
        if data is None:
            data = rqdata.get_price(order_book_id, start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = data

        dt = ExecutionContext.get_current_dt()
        str_date = dt.strftime("%Y-%m-%d")
        bar_data = data[data.index <= str_date]

        # FIXME dirty code
        bar_data = bar_data.rename(columns=self.fields_mapping)

        bar_data = bar_data[-bar_count:]

        return bar_data[field]

#
# class MyDataProxy(DataProxy):
#     def __init__(self):
#         from quantor import model, dblogic as dbl
#
#         self.db = model.new_mongo_db()
#         self.cache = {}
#
#     def get_bar(self, order_book_id, dt):
#         from quantor import model, dblogic as dbl
#         db = self.db
#
#         code, _ = order_book_id.split(".")
#         data = self.cache.get(order_book_id)
#         if data is None:
#             data = dbl.get_k_data(db, code)
#             self.cache[order_book_id] = data
#
#         try:
#             bar_data = data.ix[dt]
#         except KeyError:
#             bar_data = data[data.index <= dt].iloc[-1]
#
#         bar = BarObject()
#         bar.datetime = dt
#
#         mapping = {
#             "close": "close",
#             "open": "open",
#             "high": "high",
#             "low": "low",
#             "volume": "volume",
#         }
#         for origin_key, new_key in iteritems(mapping):
#             setattr(bar, new_key, bar_data[origin_key])
#
#         return bar


class LocalDataProxy(DataProxy):
    def __init__(self, root_dir):
        self._data_source = LocalDataSource(root_dir)
        self._cache = {}

    def get_bar(self, order_book_id, dt):
        if order_book_id not in self._cache:
            self._cache[order_book_id] = self._data_source.get_all_bars(order_book_id)

        pf = self._cache[order_book_id]
        return BarObject(self._data_source.instruments(order_book_id), pf.xs(dt.strftime("%Y-%m-%d")))

    def history(self, order_book_id, bar_count, frequency, field):
        if frequency == '1m':
            raise RuntimeError('Minute bar not supported yet!')

        if order_book_id not in self._cache:
            self._cache[order_book_id] = self._data_source.get_all_bars(order_book_id)

        df = self._cache[order_book_id]
        dt = ExecutionContext.get_current_dt()
        str_date = dt.strftime("%Y-%m-%d")
        bar_data = df[df.index <= str_date]
        return bar_data[-bar_count:][field]

    def get_yield_curve(self, start_date=None, end_date=None):
        return self._data_source.get_yield_curve(start_date, end_date)

    def get_dividend_per_share(self, order_book_id, date):
        dividend_df = self._data_source.get_dividends(order_book_id)
        df = dividend_df[dividend_df.payable_date == date]

        if df.empty:
            return 0

        return df.iloc[0]["dividend_cash_before_tax"] / df.iloc[0]["round_lot"]

    def get_trading_dates(self, start_date, end_date):
        return self._data_source.get_trading_dates(start_date, end_date)
