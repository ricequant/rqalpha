#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-27 23:40
"""

import six
import pandas as pd
import tushare as ts
from datetime import date
from dateutil.relativedelta import relativedelta

from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.data.trading_dates_mixin import TradingDatesMixin

ts.set_token("52ce20f28dbd5796c6ecf3e40d76a08756de4dd796ed914377596070")
pro = ts.pro_api()

class TushareKDataSource(BaseDataSource):

    def __init__(self, path):
        super(TushareKDataSource, self).__init__(path, {})


    @staticmethod
    def get_tushare_k_data(instrument, start_dt, end_dt):
        order_book_id = instrument.order_book_id
        code = order_book_id.split(".")[0]

        if instrument.type == 'CS':
            index = False
        elif instrument.type == 'INDX':
            index = True
        else:
            return None

        code = '000001.SZ'
        if not index:
            ts.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20180101', end_date='20181011')
            return pro.pro_bar(ts_code=code, adj='hfq', start_date=start_dt.strftime('%Y%m%d'), end_date=end_dt.strftime('%Y%m%d'))
        else:
            pro.index_daily(code, start_date='20180101', end_date='20181010')

    def get_bar(self, instrument, dt, frequency):
        if frequency != '1d':
            return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)

        bar_data = self.get_tushare_k_data(instrument, dt, dt)

        if bar_data is None or bar_data.empty:
            return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
        else:
            return bar_data.iloc[0].to_dict()

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True,
                     include_now=False, adjust_type='pre', adjust_orig=None):
        if frequency != '1d' or not skip_suspended:
            return super(TushareKDataSource, self).history_bars(instrument, bar_count, frequency, fields, dt, skip_suspended)

        trading_calendar = TradingDatesMixin(self.get_trading_calendars()).get_trading_calendar()
        start_dt_loc = trading_calendar.get_loc(dt.replace(hour=0, minute=0, second=0, microsecond=0)) - bar_count + 1
        start_dt = trading_calendar[start_dt_loc]

        bar_data = self.get_tushare_k_data(instrument, start_dt, dt)

        if bar_data is None or bar_data.empty:
            return super(TushareKDataSource, self).get_bar(instrument, dt, frequency)
        else:
            if isinstance(fields, six.string_types):
                fields = [fields]
            fields = [field for field in fields if field in bar_data.columns]

            return bar_data[fields].values

    def available_data_range(self, frequency):
        return date(2005, 1, 1), date.today() - relativedelta(days=1)