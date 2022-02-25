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
import pickle
from functools import lru_cache
from datetime import date, datetime, timedelta
from itertools import groupby
from typing import Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
import six
from rqalpha.const import INSTRUMENT_TYPE, TRADING_CALENDAR_TYPE
from rqalpha.interface import AbstractDataSource
from rqalpha.model.instrument import Instrument
from rqalpha.utils.datetime_func import (convert_date_to_int, convert_int_to_date, convert_int_to_datetime)
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.typing import DateLike
from rqalpha.environment import Environment

from rqalpha.data.base_data_source.adjust import FIELDS_REQUIRE_ADJUSTMENT, adjust_bars
from rqalpha.data.base_data_source.storage_interface import (AbstractCalendarStore, AbstractDateSet,
                                AbstractDayBarStore, AbstractDividendStore,
                                AbstractInstrumentStore)
from rqalpha.data.base_data_source.storages import (DateSet, DayBarStore, DividendStore,
                       ExchangeTradingCalendarStore, FutureDayBarStore,
                       FutureInfoStore, InstrumentStore,
                       ShareTransformationStore, SimpleFactorStore,
                       YieldCurveStore)


BAR_RESAMPLE_FIELD_METHODS = {
    "open": "first",
    "close": "last",
    "iopv": "last",
    "high": "max",
    "low": "min",
    "total_turnover": "sum",
    "volume": "sum",
    "num_trades": "sum",
    "acc_net_value": "last",
    "unit_net_value": "last",
    "discount_rate": "last",
    "settlement": "last",
    "prev_settlement": "last",
    "open_interest": "last",
    "basis_spread": "last",
    "contract_multiplier": "last",
    "strike_price": "last",
}


class BaseDataSource(AbstractDataSource):
    DEFAULT_INS_TYPES = (
        INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.INDX,
        INSTRUMENT_TYPE.PUBLIC_FUND,
    )

    def __init__(self, path, custom_future_info):
        if not os.path.exists(path):
            raise RuntimeError('bundle path {} not exist'.format(os.path.abspath(path)))

        def _p(name):
            return os.path.join(path, name)

        funds_day_bar_store = DayBarStore(_p('funds.h5'))
        self._day_bars = {
            INSTRUMENT_TYPE.CS: DayBarStore(_p('stocks.h5')),
            INSTRUMENT_TYPE.INDX: DayBarStore(_p('indexes.h5')),
            INSTRUMENT_TYPE.FUTURE: FutureDayBarStore(_p('futures.h5')),
            INSTRUMENT_TYPE.ETF: funds_day_bar_store,
            INSTRUMENT_TYPE.LOF: funds_day_bar_store
        }  # type: Dict[INSTRUMENT_TYPE, AbstractDayBarStore]

        self._future_info_store = FutureInfoStore(_p("future_info.json"), custom_future_info)

        self._instruments_stores = {}  # type: Dict[INSTRUMENT_TYPE, AbstractInstrumentStore]
        self._ins_id_or_sym_type_map = {}  # type: Dict[str, INSTRUMENT_TYPE]
        with open(_p('instruments.pk'), 'rb') as f:
            instruments = [Instrument(
                i, lambda i: self._future_info_store.get_future_info(i)["tick_size"]
            ) for i in pickle.load(f)]
        for ins_type in self.DEFAULT_INS_TYPES:
            self.register_instruments_store(InstrumentStore(instruments, ins_type))

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

        self._suspend_days = [DateSet(_p('suspended_days.h5'))]  # type: List[AbstractDateSet]
        self._st_stock_days = DateSet(_p('st_stock_days.h5'))

    def register_day_bar_store(self, instrument_type, store):
        #  type: (INSTRUMENT_TYPE, AbstractDayBarStore) -> None
        self._day_bars[instrument_type] = store

    def register_instruments_store(self, instruments_store):
        # type: (AbstractInstrumentStore) -> None
        instrument_type = instruments_store.instrument_type
        for id_or_sym in instruments_store.all_id_and_syms:
            self._ins_id_or_sym_type_map[id_or_sym] = instrument_type
        self._instruments_stores[instrument_type] = instruments_store

    def register_dividend_store(self, instrument_type, dividend_store):
        # type: (INSTRUMENT_TYPE, AbstractDividendStore) -> None
        self._dividends[instrument_type] = dividend_store

    def register_split_store(self, instrument_type, split_store):
        self._split_factors[instrument_type] = split_store

    def register_calendar_store(self, calendar_type, calendar_store):
        # type: (TRADING_CALENDAR_TYPE, AbstractCalendarStore) -> None
        self._calendar_providers[calendar_type] = calendar_store

    def append_suspend_date_set(self, date_set):
        # type: (AbstractDateSet) -> None
        self._suspend_days.append(date_set)

    @lru_cache(2048)
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
        return {t: store.get_trading_calendar() for t, store in self._calendar_providers.items()}

    def get_instruments(self, id_or_syms=None, types=None):
        # type: (Optional[Iterable[str]], Optional[Iterable[INSTRUMENT_TYPE]]) -> Iterable[Instrument]
        if id_or_syms is not None:
            ins_type_getter = lambda i: self._ins_id_or_sym_type_map.get(i)
            type_id_iter = groupby(sorted(id_or_syms, key=ins_type_getter), key=ins_type_getter)
        else:
            type_id_iter = ((t, None) for t in types or self._instruments_stores.keys())
        for ins_type, id_or_syms in type_id_iter:
            if ins_type is not None and ins_type in self._instruments_stores:
                yield from self._instruments_stores[ins_type].get_instruments(id_or_syms)

    def get_share_transformation(self, order_book_id):
        return self._share_transformation.get_share_transformation(order_book_id)

    def is_suspended(self, order_book_id, dates):
        # type: (str, Sequence[DateLike]) -> List[bool]
        for date_set in self._suspend_days:
            result = date_set.contains(order_book_id, dates)
            if result is not None:
                return result
        else:
            return [False] * len(dates)

    def is_st_stock(self, order_book_id, dates):
        result = self._st_stock_days.contains(order_book_id, dates)
        return result if result is not None else [False] * len(dates)

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

    OPEN_AUCTION_BAR_FIELDS = ["datetime", "open", "limit_up", "limit_down", "volume", "total_turnover"]

    def get_open_auction_bar(self, instrument, dt):
        # type: (Instrument, Union[datetime, date]) -> Dict
        day_bar = self.get_bar(instrument, dt, "1d")
        bar = {k: day_bar[k] if k in day_bar.dtype.names else np.nan for k in self.OPEN_AUCTION_BAR_FIELDS}
        bar["last"] = bar["open"]
        return bar

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

    def _update_weekly_trading_date_index(self, idx):
        env = Environment.get_instance()
        if env.data_proxy.is_trading_date(idx):
            return idx
        return env.data_proxy.get_previous_trading_date(idx)

    def resample_week_bars(self, bars, bar_count, fields):
        df_bars = pd.DataFrame(bars)
        df_bars['datetime'] = df_bars.apply(lambda x: convert_int_to_datetime(x['datetime']), axis=1)
        df_bars = df_bars.set_index('datetime')
        nead_fields = fields
        if isinstance(nead_fields, str):
            nead_fields = [nead_fields]
        hows = {field: BAR_RESAMPLE_FIELD_METHODS[field] for field in nead_fields if field in BAR_RESAMPLE_FIELD_METHODS}
        df_bars = df_bars.resample('W-Fri').agg(hows)
        df_bars.index = df_bars.index.map(self._update_weekly_trading_date_index)
        df_bars = df_bars[~df_bars.index.duplicated(keep='first')]
        df_bars.sort_index(inplace=True)
        df_bars = df_bars[-bar_count:]
        df_bars = df_bars.reset_index()
        df_bars['datetime'] = df_bars.apply(lambda x: np.uint64(convert_date_to_int(x['datetime'].date())), axis=1)
        df_bars = df_bars.set_index('datetime')
        bars = df_bars.to_records()
        return bars

    def history_bars(self, instrument, bar_count, frequency, fields, dt,
                     skip_suspended=True, include_now=False,
                     adjust_type='pre', adjust_orig=None):

        if frequency != '1d' and frequency != '1w':
            raise NotImplementedError

        if skip_suspended and instrument.type == 'CS':
            bars = self._filtered_day_bars(instrument)
        else:
            bars = self._all_day_bars_of(instrument)

        if not self._are_fields_valid(fields, bars.dtype.names):
            raise RQInvalidArgument("invalid fields: {}".format(fields))

        if len(bars) <= 0:
            return bars

        if frequency == '1w':
            if include_now:
                dt = np.uint64(convert_date_to_int(dt))
                i = bars['datetime'].searchsorted(dt, side='right')
            else:
                monday = dt - timedelta(days=dt.weekday())
                monday = np.uint64(convert_date_to_int(monday))
                i = bars['datetime'].searchsorted(monday, side='left')

            left = i - bar_count * 5 if i >= bar_count * 5 else 0
            bars = bars[left:i]

            if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
                # 期货及指数无需复权
                week_bars = self.resample_week_bars(bars, bar_count, fields)
                return week_bars if fields is None else week_bars[fields]

            if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
                week_bars = self.resample_week_bars(bars, bar_count, fields)
                return week_bars if fields is None else week_bars[fields]

            adjust_bars_date = adjust_bars(bars, self.get_ex_cum_factor(instrument.order_book_id),
                                           fields, adjust_type, adjust_orig)
            adjust_week_bars = self.resample_week_bars(adjust_bars_date, bar_count, fields)
            return adjust_week_bars if fields is None else adjust_week_bars[fields]
        dt = np.uint64(convert_date_to_int(dt))
        i = bars['datetime'].searchsorted(dt, side='right')
        left = i - bar_count if i >= bar_count else 0
        bars = bars[left:i]
        if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
            # 期货及指数无需复权
            return bars if fields is None else bars[fields]

        if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
            return bars if fields is None else bars[fields]

        bars = adjust_bars(bars, self.get_ex_cum_factor(instrument.order_book_id),
                           fields, adjust_type, adjust_orig)

        return bars if fields is None else bars[fields]

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    @lru_cache(2048)
    def get_split(self, instrument):
        try:
            splilt_store = self._split_factors[instrument.type]
        except KeyError:
            return None

        return splilt_store.get_factors(instrument.order_book_id)

    def available_data_range(self, frequency):
        # FIXME
        from rqalpha.const import DEFAULT_ACCOUNT_TYPE
        accounts = Environment.get_instance().config.base.accounts
        if not (DEFAULT_ACCOUNT_TYPE.STOCK in accounts or DEFAULT_ACCOUNT_TYPE.FUTURE in accounts):
            return date.min, date.max
        if frequency in ['tick', '1d']:
            s, e = self._day_bars[INSTRUMENT_TYPE.INDX].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

    def get_yield_curve(self, start_date, end_date, tenor=None):
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor=tenor)

    def get_commission_info(self, instrument):
        return self._future_info_store.get_future_info(instrument)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        raise NotImplementedError

    def history_ticks(self, instrument, count, dt):
        raise NotImplementedError
