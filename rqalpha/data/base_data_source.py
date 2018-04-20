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

import os
import six
import numpy as np

from rqalpha.interface import AbstractDataSource
from rqalpha.const import MARGIN_TYPE
from rqalpha.utils.py2 import lru_cache
from rqalpha.utils.datetime_func import convert_date_to_int, convert_int_to_date
from rqalpha.utils.i18n import gettext as _

from rqalpha.data.future_info_cn import CN_FUTURE_INFO
from rqalpha.data.converter import StockBarConverter, IndexBarConverter
from rqalpha.data.converter import FutureDayBarConverter, FundDayBarConverter, PublicFundDayBarConverter
from rqalpha.data.daybar_store import DayBarStore
from rqalpha.data.date_set import DateSet
from rqalpha.data.dividend_store import DividendStore
from rqalpha.data.instrument_store import InstrumentStore
from rqalpha.data.trading_dates_store import TradingDatesStore
from rqalpha.data.yield_curve_store import YieldCurveStore
from rqalpha.data.simple_factor_store import SimpleFactorStore
from rqalpha.data.adjust import adjust_bars, FIELDS_REQUIRE_ADJUSTMENT
from rqalpha.data.public_fund_commission import PUBLIC_FUND_COMMISSION


class BaseDataSource(AbstractDataSource):
    def __init__(self, path):
        if not os.path.exists(path):
            raise RuntimeError('bundle path {} not exist'.format(os.path.abspath(path)))

        def _p(name):
            return os.path.join(path, name)

        self._day_bars = [
            DayBarStore(_p('stocks.bcolz'), StockBarConverter),
            DayBarStore(_p('indexes.bcolz'), IndexBarConverter),
            DayBarStore(_p('futures.bcolz'), FutureDayBarConverter),
            DayBarStore(_p('funds.bcolz'), FundDayBarConverter),
        ]

        self._instruments = InstrumentStore(_p('instruments.pk'))
        self._dividends = DividendStore(_p('original_dividends.bcolz'))
        self._trading_dates = TradingDatesStore(_p('trading_dates.bcolz'))
        self._yield_curve = YieldCurveStore(_p('yield_curve.bcolz'))
        self._split_factor = SimpleFactorStore(_p('split_factor.bcolz'))
        self._ex_cum_factor = SimpleFactorStore(_p('ex_cum_factor.bcolz'))

        self._st_stock_days = DateSet(_p('st_stock_days.bcolz'))
        self._suspend_days = DateSet(_p('suspended_days.bcolz'))

        self.get_yield_curve = self._yield_curve.get_yield_curve
        self.get_risk_free_rate = self._yield_curve.get_risk_free_rate
        if os.path.exists(_p('public_funds.bcolz')):
            self._day_bars.append(DayBarStore(_p('public_funds.bcolz'), PublicFundDayBarConverter))
            self._public_fund_dividends = DividendStore(_p('public_fund_dividends.bcolz'))
            self._non_subscribable_days = DateSet(_p('non_subscribable_days.bcolz'))
            self._non_redeemable_days = DateSet(_p('non_redeemable_days.bcolz'))

    def get_dividend(self, order_book_id, public_fund=False):
        if public_fund:
            return self._public_fund_dividends.get_dividend(order_book_id)
        return self._dividends.get_dividend(order_book_id)

    def get_trading_minutes_for(self, order_book_id, trading_dt):
        raise NotImplementedError

    def get_trading_calendar(self):
        return self._trading_dates.get_trading_calendar()

    def get_all_instruments(self):
        return self._instruments.get_all_instruments()

    def is_suspended(self, order_book_id, dates):
        return self._suspend_days.contains(order_book_id, dates)

    def is_st_stock(self, order_book_id, dates):
        return self._st_stock_days.contains(order_book_id, dates)

    INSTRUMENT_TYPE_MAP = {
        'CS': 0,
        'INDX': 1,
        'Future': 2,
        'ETF': 3,
        'LOF': 3,
        'FenjiA': 3,
        'FenjiB': 3,
        'FenjiMu': 3,
        'PublicFund': 4
    }

    def _index_of(self, instrument):
        return self.INSTRUMENT_TYPE_MAP[instrument.type]

    @lru_cache(None)
    def _all_day_bars_of(self, instrument):
        i = self._index_of(instrument)
        return self._day_bars[i].get_bars(instrument.order_book_id, fields=None)

    @lru_cache(None)
    def _filtered_day_bars(self, instrument):
        bars = self._all_day_bars_of(instrument)
        if bars is None:
            return None
        return bars[bars['volume'] > 0]

    def get_bar(self, instrument, dt, frequency):
        if frequency != '1d':
            raise NotImplementedError

        bars = self._all_day_bars_of(instrument)
        if bars is None:
            return
        dt = np.uint64(convert_date_to_int(dt))
        pos = bars['datetime'].searchsorted(dt)
        if pos >= len(bars) or bars['datetime'][pos] != dt:
            return None

        return bars[pos]

    def get_settle_price(self, instrument, date):
        bar = self.get_bar(instrument, date, '1d')
        if bar is None:
            return np.nan
        return bar['settlement']

    @staticmethod
    def _are_fields_valid(fields, valid_fields):
        if fields is None:
            return True
        if isinstance(fields, six.string_types):
            return fields in valid_fields
        for field in fields:
            if field not in valid_fields:
                return False
        return True

    def get_ex_cum_factor(self, order_book_id):
        return self._ex_cum_factor.get_factors(order_book_id)

    def history_bars(self, instrument, bar_count, frequency, fields, dt,
                     skip_suspended=True, include_now=False,
                     adjust_type='pre', adjust_orig=None):
        if frequency != '1d':
            raise NotImplementedError

        if skip_suspended and instrument.type == 'CS':
            bars = self._filtered_day_bars(instrument)
        else:
            bars = self._all_day_bars_of(instrument)

        if bars is None or not self._are_fields_valid(fields, bars.dtype.names):
            return None

        dt = np.uint64(convert_date_to_int(dt))
        i = bars['datetime'].searchsorted(dt, side='right')
        left = i - bar_count if i >= bar_count else 0
        bars = bars[left:i]
        if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
            # 期货及指数无需复权
            return bars if fields is None else bars[fields]

        if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
            return bars if fields is None else bars[fields]

        return adjust_bars(bars, self.get_ex_cum_factor(instrument.order_book_id),
                           fields, adjust_type, adjust_orig)

    def get_yield_curve(self, start_date, end_date, tenor=None):
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor)

    def get_risk_free_rate(self, start_date, end_date):
        return self._yield_curve.get_risk_free_rate(start_date, end_date)

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    def get_split(self, order_book_id):
        return self._split_factor.get_factors(order_book_id)

    def available_data_range(self, frequency):
        if frequency in ['tick', '1d']:
            s, e = self._day_bars[self.INSTRUMENT_TYPE_MAP['INDX']].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

        raise NotImplementedError

    def get_margin_info(self, instrument):
        return {
            'margin_type': MARGIN_TYPE.BY_MONEY,
            'long_margin_ratio': instrument.margin_rate,
            'short_margin_ratio': instrument.margin_rate,
        }

    def get_commission_info(self, instrument):
        return CN_FUTURE_INFO[instrument.underlying_symbol]['speculation']

    def get_ticks(self, order_book_id, date):
        raise NotImplementedError

    def public_fund_commission(self, instrument, buy):
        if buy:
            return PUBLIC_FUND_COMMISSION[instrument.fund_type]['Buy']
        else:
            return PUBLIC_FUND_COMMISSION[instrument.fund_type]['Sell']

    def non_subscribable(self, order_book_id, dates):
        return self._non_subscribable_days.contains(order_book_id, dates)

    def non_redeemable(self, order_book_id, dates):
        return self._non_redeemable_days.contains(order_book_id, dates)

    def get_tick_size(self, instrument):
        if instrument.type in ['CS', 'INDX']:
            return 0.01
        elif instrument.type in ['ETF', 'LOF', 'FenjiB', 'FenjiA', 'FenjiMu']:
            return 0.001
        elif instrument.type == 'Future':
            return CN_FUTURE_INFO[instrument.underlying_symbol]['speculation']['tick_size']
        else:
            # NOTE: you can override get_tick_size in your custom data source
            raise RuntimeError(_("Unsupported instrument type for tick size"))
