# -*- coding: utf-8 -*-
import abc

from six import with_metaclass
import pandas as pd

from .bar import BarObject


class DataProxy(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_data(self, order_book_id, dt):
        raise NotImplementedError


class RqDataProxy(DataProxy):
    def __init__(self):
        import rqdata
        self.rqdata = rqdata
        rqdata.init()
        self.cache = {}

    def get_data(self, order_book_id, dt):
        # should use a better cache here
        rqdata = self.rqdata

        data = self.cache.get(order_book_id)
        if data is None:
            data = rqdata.get_price(order_book_id)
            self.cache[order_book_id] = data

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
        for origin_key, new_key in mapping.items():
            setattr(bar, new_key, bar_data[origin_key])

        return bar


class MyDataProxy(DataProxy):
    def __init__(self):
        from quantor import model, dblogic as dbl

        self.db = model.new_mongo_db()
        self.cache = {}

    def get_data(self, order_book_id, dt):
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

        return bar
