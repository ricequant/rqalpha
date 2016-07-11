# -*- coding: utf-8 -*-
import abc

from six import with_metaclass, iteritems
import pandas as pd

from .bar import BarObject
from ..utils.context import ExecutionContext


class DataProxy(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_bar(self, order_book_id, dt):
        raise NotImplementedError

    def latest_bar(self, order_book_id):
        dt = ExecutionContext.get_strategy().now

        return self.get_bar(order_book_id, dt)

    @abc.abstractmethod
    def get_yield_curve(self, start_date=None, end_date=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_dividend(self, order_book_id, start_date=None, end_date=None):
        raise NotImplementedError


class RqDataProxy(DataProxy):
    def __init__(self):
        import rqdata
        self.rqdata = rqdata
        rqdata.init()
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

        bar = BarObject()
        bar.datetime = dt

        mapping = {
            "ClosingPx": "close",
            "OpeningPx": "open",
            "HighPx": "high",
            "LowPx": "low",
            "TotalVolumeTraded": "volume",
            "TotalTurnover": "total_turnover",
            # TODO: fill bar
        }
        for origin_key, new_key in iteritems(mapping):
            setattr(bar, new_key, bar_data[origin_key])

        return bar

    def get_yield_curve(self, start_date=None, end_date=None):
        rqdata = self.rqdata

        cache_key = "get_yield_curve"
        data = self.cache.get(cache_key)
        if data is None:
            data = rqdata.get_yield_curve(start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = data
        return data

    def get_dividend(self, order_book_id, start_date=None, end_date=None):
        rqdata = self.rqdata

        cache_key = "get_dividend:%s" % order_book_id
        data = self.cache.get(cache_key)
        if data is None:
            data = rqdata.get_dividend(order_book_id, start_date="2006-01-01", end_date="2020-01-01")
            self.cache[cache_key] = data
        return data


class MyDataProxy(DataProxy):
    def __init__(self):
        from quantor import model, dblogic as dbl

        self.db = model.new_mongo_db()
        self.cache = {}

    def get_bar(self, order_book_id, dt):
        from quantor import model, dblogic as dbl
        db = self.db

        code, _ = order_book_id.split(".")
        data = self.cache.get(order_book_id)
        if data is None:
            data = dbl.get_k_data(db, code)
            self.cache[order_book_id] = data

        try:
            bar_data = data.ix[dt]
        except KeyError:
            bar_data = data[data.index <= dt].iloc[-1]

        bar = BarObject()
        bar.datetime = dt

        mapping = {
            "close": "close",
            "open": "open",
            "high": "high",
            "low": "low",
            "volume": "volume",
        }
        for origin_key, new_key in iteritems(mapping):
            setattr(bar, new_key, bar_data[origin_key])

        return bar
