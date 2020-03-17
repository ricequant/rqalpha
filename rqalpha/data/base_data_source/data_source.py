# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。
import os
from datetime import date, datetime
from typing import Dict, List, Union, Optional

import six
import numpy as np
import pandas as pd

from rqalpha.interface import AbstractDataSource
from rqalpha.utils.py2 import lru_cache
from rqalpha.utils.datetime_func import convert_date_to_int, convert_int_to_date
from rqalpha.utils.i18n import gettext as _
from rqalpha.const import INSTRUMENT_TYPE, TRADING_CALENDAR_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils.exception import RQInvalidArgument

from .storages import (
    InstrumentStore, ShareTransformationStore, FutureInfoStore, AbstractDayBarStore, AbstractInstrumentStore,
    AbstractCalendarStore, ExchangeTradingCalendarStore
)
from .h5_storages import (
    DayBarStore, DividendStore, YieldCurveStore, SimpleFactorStore
)
from .date_set import DateSet
from .adjust import adjust_bars, FIELDS_REQUIRE_ADJUSTMENT


class BaseDataSource(AbstractDataSource):
    def __init__(self, path, custom_future_info):
        if not os.path.exists(path):
            raise RuntimeError('bundle path {} not exist'.format(os.path.abspath(path)))

        def _p(name):
            return os.path.join(path, name)

        self._day_bars = {
            INSTRUMENT_TYPE.CS: DayBarStore(_p('stocks.h5')),
            INSTRUMENT_TYPE.INDX: DayBarStore(_p('indexes.h5')),
            INSTRUMENT_TYPE.FUTURE: DayBarStore(_p('futures.h5')),
        }  # type: Dict[INSTRUMENT_TYPE, AbstractDayBarStore]
        funds_day_bar_store = DayBarStore(_p('funds.h5'))
        for instrument_type in (
            INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF
        ):
            self.register_day_bar_store(instrument_type, funds_day_bar_store)

        self._instruments = InstrumentStore(_p('instruments.pk')).get_all_instruments()  # type: List[Instrument]

        dividend_store = DividendStore(_p('dividends.h5'))
        self._dividends = {
            INSTRUMENT_TYPE.CS: dividend_store,
            INSTRUMENT_TYPE.ETF: dividend_store,
            INSTRUMENT_TYPE.LOF: dividend_store,
        }
        self._calendar_providers = {
            TRADING_CALENDAR_TYPE.EXCHANGE: ExchangeTradingCalendarStore(_p("trading_dates.npy"))
        }
        self._yield_curve = YieldCurveStore(_p('yield_curve.h5'))

        split_store = SimpleFactorStore(_p('split_factor.h5'))
        self._split_factors = {
            INSTRUMENT_TYPE.CS: split_store,
            INSTRUMENT_TYPE.ETF: split_store,
            INSTRUMENT_TYPE.LOF: split_store,
        }
        self._ex_cum_factor = SimpleFactorStore(_p('ex_cum_factor.h5'))
        self._share_transformation = ShareTransformationStore(_p('share_transformation.json'))

        self._st_stock_days = DateSet(_p('st_stock_days.h5'))
        self._suspend_days = DateSet(_p('suspended_days.h5'))

        self._future_info_store = FutureInfoStore(_p("future_info.json"), custom_future_info)

    def register_day_bar_store(self, instrument_type, store):
        #  type: (INSTRUMENT_TYPE, AbstractDayBarStore) -> None
        self._day_bars[instrument_type] = store

    def register_instruments_store(self, instruments_store):
        # type: (AbstractInstrumentStore) -> None
        self._instruments.extend(instruments_store.get_all_instruments())

    def register_dividend_store(self, instrument_type, dividend_store):
        # type: (INSTRUMENT_TYPE, DividendStore) -> None
        self._dividends[instrument_type] = dividend_store

    def register_split_store(self, instrument_type, split_store):
        self._split_factors[instrument_type] = split_store

    def register_calendar_store(self, calendar_type, calendar_store):
        # type: (TRADING_CALENDAR_TYPE, AbstractCalendarStore) -> None
        self._calendar_providers[calendar_type] = calendar_store

    def get_dividend(self, instrument):
        try:
            dividend_store = self._dividends[instrument.type]
        except KeyError:
            return None

        return dividend_store.get_dividend(instrument.order_book_id)

    def get_trading_minutes_for(self, order_book_id, trading_dt):
        raise NotImplementedError

    def get_trading_calendars(self):
        # type: () -> Dict[TRADING_CALENDAR_TYPE, pd.DatetimeIndex]
        return {t: store.get_trading_calendar() for t, store in six.iteritems(self._calendar_providers)}

    def get_all_instruments(self):
        return self._instruments

    def get_share_transformation(self, order_book_id):
        return self._share_transformation.get_share_transformation(order_book_id)

    def is_suspended(self, order_book_id, dates):
        return self._suspend_days.contains(order_book_id, dates)

    def is_st_stock(self, order_book_id, dates):
        return self._st_stock_days.contains(order_book_id, dates)

    @lru_cache(None)
    def _all_day_bars_of(self, instrument):
        return self._day_bars[instrument.type].get_bars(instrument.order_book_id)

    @lru_cache(None)
    def _filtered_day_bars(self, instrument):
        bars = self._all_day_bars_of(instrument)
        return bars[bars['volume'] > 0]

    def get_bar(self, instrument, dt, frequency):
        # type: (Instrument, Union[datetime, date], str) -> Optional[np.ndarray]
        if frequency != '1d':
            raise NotImplementedError

        bars = self._all_day_bars_of(instrument)
        if len(bars) <= 0:
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

        if not self._are_fields_valid(fields, bars.dtype.names):
            raise RQInvalidArgument("invalid fileds: {}".format(fields))

        if len(bars) <= 0:
            return bars

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

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    def get_split(self, instrument):
        try:
            splilt_store = self._split_factors[instrument.type]
        except KeyError:
            return None

        return splilt_store.get_factors(instrument.order_book_id)

    def available_data_range(self, frequency):
        if frequency in ['tick', '1d']:
            s, e = self._day_bars[INSTRUMENT_TYPE.INDX].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

    def get_ticks(self, order_book_id, date):
        raise NotImplementedError

    def get_tick_size(self, instrument):
        if instrument.type == 'CS':
            return 0.01
        elif instrument.type == "INDX":
            return 0.01
        elif instrument.type in ['ETF', 'LOF', 'FenjiB', 'FenjiA', 'FenjiMu']:
            return 0.001
        elif instrument.type == 'Future':
            return self._future_info_store.get_future_info(instrument)["tick_size"]
        else:
            # NOTE: you can override get_tick_size in your custom data source
            raise RuntimeError(_("Unsupported instrument type for tick size"))

    def get_yield_curve(self, start_date, end_date, tenor=None):
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor=tenor)

    def get_commission_info(self, instrument):
        return self._future_info_store.get_future_info(instrument)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        raise NotImplementedError

    def history_ticks(self, instrument, count, dt):
        raise NotImplementedError
