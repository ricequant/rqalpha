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
from collections import ChainMap
import os
from datetime import date, datetime, timedelta
from itertools import chain, repeat
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Union, cast, Tuple

try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable

import numpy as np
import pandas as pd
import six
from rqalpha.utils.i18n import gettext as _
from rqalpha.const import INSTRUMENT_TYPE, MARKET, TRADING_CALENDAR_TYPE
from rqalpha.interface import AbstractDataSource, ExchangeRate
from rqalpha.model.instrument import Instrument
from rqalpha.utils.datetime_func import (convert_date_to_int, convert_int_to_date, convert_int_to_datetime, convert_dt_to_int)
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.typing import DateLike
from rqalpha.utils.logger import system_log
from rqalpha.environment import Environment
from rqalpha.data.base_data_source.adjust import FIELDS_REQUIRE_ADJUSTMENT, adjust_bars
from rqalpha.data.base_data_source.storage_interface import (AbstractCalendarStore, AbstractDateSet,
                                AbstractDayBarStore, AbstractDividendStore,
                                AbstractInstrumentStore, AbstractSimpleFactorStore)
from rqalpha.data.base_data_source.storages import (DateSet, DayBarStore, DividendStore,
                       ExchangeTradingCalendarStore, FutureDayBarStore,
                       FutureInfoStore, ShareTransformationStore, SimpleFactorStore,
                       YieldCurveStore, FuturesTradingParameters, load_instruments_from_pkl)


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


@runtime_checkable
class BaseDataSourceProtocol(Protocol):
    def register_day_bar_store(self, instrument_type: INSTRUMENT_TYPE, store: AbstractDayBarStore, market: MARKET = MARKET.CN) -> None:
        ...
    def register_instruments(self, instruments: Iterable[Instrument]) -> None:
        ...
    def register_dividend_store(self, instrument_type: INSTRUMENT_TYPE, dividend_store: AbstractDividendStore, market: MARKET = MARKET.CN) -> None:
        ...
    def register_split_store(self, instrument_type: INSTRUMENT_TYPE, split_store: AbstractSimpleFactorStore, market: MARKET = MARKET.CN) -> None:
        ...
    def register_calendar_store(self, calendar_type: TRADING_CALENDAR_TYPE, calendar_store: AbstractCalendarStore) -> None:
        ...
    def register_ex_factor_store(self, instrument_type: INSTRUMENT_TYPE, ex_factor_store: AbstractSimpleFactorStore, market: MARKET = MARKET.CN) -> None:
        ...


class BaseDataSource(AbstractDataSource):
    DEFAULT_INS_TYPES = (
        INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.INDX,
        INSTRUMENT_TYPE.PUBLIC_FUND, INSTRUMENT_TYPE.REITs
    )

    def __init__(self, base_config) -> None:
        path = base_config.data_bundle_path
        custom_future_info = getattr(base_config, "future_info", {})
        if not os.path.exists(path):
            raise RuntimeError('bundle path {} not exist'.format(os.path.abspath(path)))

        def _p(name):
            return os.path.join(path, name)
        
        # static registered storages
        self._future_info_store = FutureInfoStore(_p("future_info.json"), custom_future_info)
        self._yield_curve = YieldCurveStore(_p('yield_curve.h5'))
        self._share_transformation = ShareTransformationStore(_p('share_transformation.json'))
        self._suspend_days = [DateSet(_p('suspended_days.h5'))]  # type: List[AbstractDateSet]
        self._st_stock_days = DateSet(_p('st_stock_days.h5'))

        # dynamic registered storages
        self._ins_id_or_sym_type_map: Dict[str, INSTRUMENT_TYPE] = {}
        self._day_bar_stores: Dict[Tuple[INSTRUMENT_TYPE, MARKET], AbstractDayBarStore] = {}
        self._dividend_stores: Dict[Tuple[INSTRUMENT_TYPE, MARKET], AbstractDividendStore] = {}
        self._split_stores: Dict[Tuple[INSTRUMENT_TYPE, MARKET], AbstractSimpleFactorStore] = {}
        self._calendar_stores: Dict[TRADING_CALENDAR_TYPE, AbstractCalendarStore] = {}
        self._ex_factor_stores: Dict[Tuple[INSTRUMENT_TYPE, MARKET], AbstractSimpleFactorStore] = {}

        # instruments
        self._id_instrument_map: Dict[str, Dict[datetime, Instrument]] = {}
        self._sym_instrument_map: Dict[str, Dict[datetime, Instrument]] = {}
        self._id_or_sym_instrument_map: Mapping[str, Dict[datetime, Instrument]] = ChainMap(self._id_instrument_map, self._sym_instrument_map)
        self._grouped_instruments: Dict[INSTRUMENT_TYPE, Dict[datetime, Instrument]] = {}

        # register instruments
        self.register_instruments(load_instruments_from_pkl(_p('instruments.pk'), self._future_info_store))

        # register day bar stores
        funds_day_bar_store = DayBarStore(_p('funds.h5'))
        for ins_type, store in chain([
            (INSTRUMENT_TYPE.CS, DayBarStore(_p('stocks.h5'))),
            (INSTRUMENT_TYPE.INDX, DayBarStore(_p('indexes.h5'))),
            (INSTRUMENT_TYPE.FUTURE, FutureDayBarStore(_p('futures.h5'))),
        ], zip([INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.REITs], repeat(funds_day_bar_store))):
            self.register_day_bar_store(ins_type, store)

        # register dividends and split factors stores
        dividend_store = DividendStore(_p('dividends.h5'))
        split_store = SimpleFactorStore(_p('split_factor.h5'))
        ex_factor_store = SimpleFactorStore(_p('ex_cum_factor.h5'))
        for ins_type in [INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.REITs]:
            self.register_dividend_store(ins_type, dividend_store)
            self.register_split_store(ins_type, split_store)
            self.register_ex_factor_store(ins_type, ex_factor_store)

        # register calendar stores
        self.register_calendar_store(TRADING_CALENDAR_TYPE.CN_STOCK, ExchangeTradingCalendarStore(_p("trading_dates.npy")))

    def register_day_bar_store(self, instrument_type: INSTRUMENT_TYPE, store: AbstractDayBarStore, market: MARKET = MARKET.CN):
        self._day_bar_stores[instrument_type, market] = store

    def register_instruments(self, instruments: Iterable[Instrument]):
        for ins in instruments:
            self._id_instrument_map.setdefault(ins.order_book_id, {})[ins.listed_date] = ins
            self._sym_instrument_map.setdefault(ins.symbol, {})[ins.listed_date] = ins
            self._grouped_instruments.setdefault(ins.type, {})[ins.listed_date] = ins
    
    def register_dividend_store(self, instrument_type: INSTRUMENT_TYPE, dividend_store: AbstractDividendStore, market: MARKET = MARKET.CN):
        self._dividend_stores[instrument_type, market] = dividend_store

    def register_split_store(self, instrument_type: INSTRUMENT_TYPE, split_store: AbstractSimpleFactorStore, market: MARKET = MARKET.CN):
        self._split_stores[instrument_type, market] = split_store

    def register_calendar_store(self, calendar_type: TRADING_CALENDAR_TYPE, calendar_store: AbstractCalendarStore):
        self._calendar_stores[calendar_type] = calendar_store

    def register_ex_factor_store(self, instrument_type: INSTRUMENT_TYPE, ex_factor_store: AbstractSimpleFactorStore, market: MARKET = MARKET.CN):
        self._ex_factor_stores[instrument_type, market] = ex_factor_store

    def append_suspend_date_set(self, date_set):
        # type: (AbstractDateSet) -> None
        self._suspend_days.append(date_set)

    @lru_cache(2048)
    def get_dividend(self, instrument):
        try:
            dividend_store = self._dividend_stores[instrument.type, instrument.market]
        except KeyError:
            return None

        return dividend_store.get_dividend(instrument.order_book_id)

    def get_trading_minutes_for(self, instrument, trading_dt):
        raise NotImplementedError

    def get_trading_calendars(self) -> Dict[TRADING_CALENDAR_TYPE, pd.DatetimeIndex]:
        return {t: store.get_trading_calendar() for t, store in self._calendar_stores.items()}

    def get_instruments(self, id_or_syms: Optional[Iterable[str]] = None, types: Optional[Iterable[INSTRUMENT_TYPE]] = None) -> Iterable[Instrument]:
        if id_or_syms is not None:
            seen = set()
            for i in id_or_syms:
                v = self._id_or_sym_instrument_map.get(i)
                if v:
                    for ins in v.values():
                        if ins not in seen:
                            seen.add(ins)
                            yield ins
        else:
            for t in types or self._grouped_instruments.keys():
                yield from self._grouped_instruments[t].values()

    def get_share_transformation(self, order_book_id):
        return self._share_transformation.get_share_transformation(order_book_id)

    def is_suspended(self, order_book_id: str, dates: Sequence[DateLike]) -> List[bool]:
        for date_set in self._suspend_days:
            result = date_set.contains(order_book_id, dates)
            if result is not None:
                return result
        else:
            return [False] * len(dates)

    def is_st_stock(self, order_book_id: str, dates: Sequence[DateLike]) -> List[bool]:
        result = self._st_stock_days.contains(order_book_id, dates)
        return result if result is not None else [False] * len(dates)

    @lru_cache(None)
    def _all_day_bars_of(self, instrument):
        return self._day_bar_stores[instrument.type, instrument.market].get_bars(instrument.order_book_id)

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
        dt_int = np.uint64(convert_date_to_int(dt))
        pos = bars['datetime'].searchsorted(dt_int)
        if pos >= len(bars) or bars['datetime'][pos] != dt_int:
            return None

        return bars[pos]

    OPEN_AUCTION_BAR_FIELDS = ["datetime", "open", "limit_up", "limit_down", "volume", "total_turnover"]

    def get_open_auction_bar(self, instrument, dt):
        # type: (Instrument, Union[datetime, date]) -> Dict
        day_bar = self.get_bar(instrument, dt, "1d")
        if day_bar is None:
            bar = dict.fromkeys(self.OPEN_AUCTION_BAR_FIELDS, np.nan)
        else:
            bar = {k: day_bar[k] if k in day_bar.dtype.names else np.nan for k in self.OPEN_AUCTION_BAR_FIELDS}
        bar["last"] = bar["open"]  # type: ignore
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

    @lru_cache(1024)
    def get_ex_cum_factor(self, instrument: Instrument):
        try:
            ex_factor_store = self._ex_factor_stores[instrument.type, instrument.market]
        except KeyError:
            return None
        factors = ex_factor_store.get_factors(instrument.order_book_id)
        if factors is None:
            return None
        # 考虑代码复用的情况，需要过滤掉不在上市日期范围内到数据
        factors = factors[
            (factors["start_date"] >= convert_dt_to_int(instrument.listed_date)) & 
            (factors["start_date"] <= convert_dt_to_int(instrument.de_listed_date))
        ]
        if len(factors) == 0:
            return None
        if factors["start_date"][0] != 0:
            # kind of dirty，强行设置初始值为 1
            factors = np.concatenate([np.array([(0, 1.0)], dtype=factors.dtype), factors])
        return factors

    def _update_weekly_trading_date_index(self, idx):
        env = Environment.get_instance()
        if env.data_proxy.is_trading_date(idx):
            return idx
        return env.data_proxy.get_previous_trading_date(idx)

    def resample_week_bars(self, bars, bar_count: Optional[int], fields: Union[str, List[str]]):
        df_bars: pd.DataFrame = pd.DataFrame(bars)
        df_bars['datetime'] = df_bars.apply(lambda x: convert_int_to_datetime(x['datetime']), axis=1)
        df_bars = df_bars.set_index('datetime')
        nead_fields = fields
        if isinstance(nead_fields, str):
            nead_fields = [nead_fields]
        hows = {field: BAR_RESAMPLE_FIELD_METHODS[field] for field in nead_fields if field in BAR_RESAMPLE_FIELD_METHODS}
        df_bars = df_bars.resample('W-Fri').agg(hows)  # type: ignore
        df_bars.index = df_bars.index.map(self._update_weekly_trading_date_index)
        df_bars = cast(pd.DataFrame, df_bars[~df_bars.index.duplicated(keep='first')])
        df_bars.sort_index(inplace=True)
        if bar_count is not None:
            df_bars = cast(pd.DataFrame, df_bars[-bar_count:])
        df_bars = df_bars.reset_index()
        df_bars['datetime'] = df_bars.apply(lambda x: np.uint64(convert_date_to_int(x['datetime'].date())), axis=1)  # type: ignore
        df_bars = df_bars.set_index('datetime')
        bars = df_bars.to_records()
        return bars

    def history_bars(
        self, 
        instrument: Instrument, 
        bar_count: Optional[int], 
        frequency: str, 
        fields: Union[str, List[str], None], 
        dt: datetime, 
        skip_suspended: bool = True,
        include_now: bool = False, 
        adjust_type: str = 'pre', 
        adjust_orig: Optional[datetime] = None
    ) -> Optional[np.ndarray]:

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
                i = bars['datetime'].searchsorted(np.uint64(convert_date_to_int(dt)), side='right')
            else:
                monday = dt - timedelta(days=dt.weekday())
                monday = np.uint64(convert_date_to_int(monday))
                i = bars['datetime'].searchsorted(monday, side='left')
            
            if bar_count is None:
                left = 0
            else:
                left = i - bar_count * 5 if i >= bar_count * 5 else 0
            bars = bars[left:i]

            resample_fields: Union[str, List[str]] = list(bars.dtype.names) if fields is None else fields
            if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
                # 期货及指数无需复权
                week_bars = self.resample_week_bars(bars, bar_count, resample_fields)
                return week_bars if fields is None else week_bars[fields]

            if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
                week_bars = self.resample_week_bars(bars, bar_count, resample_fields)
                return week_bars if fields is None else week_bars[fields]

            adjust_bars_date = adjust_bars(bars, self.get_ex_cum_factor(instrument),
                                           fields, adjust_type, adjust_orig)
            adjust_week_bars = self.resample_week_bars(adjust_bars_date, bar_count, resample_fields)
            return adjust_week_bars if fields is None else adjust_week_bars[fields]
        i = bars['datetime'].searchsorted(np.uint64(convert_date_to_int(dt)), side='right')
        if bar_count is None:
            left = 0
        else:
            left = i - bar_count if i >= bar_count else 0
        bars = bars[left:i]
        if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
            # 期货及指数无需复权
            return bars if fields is None else bars[fields]

        if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
            return bars if fields is None else bars[fields]

        bars = adjust_bars(bars, self.get_ex_cum_factor(instrument),
                           fields, adjust_type, adjust_orig)

        return bars if fields is None else bars[fields]

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    @lru_cache(2048)
    def get_split(self, instrument):
        try:
            splilt_store = self._split_stores[instrument.type, instrument.market]
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
            s, e = self._day_bar_stores[INSTRUMENT_TYPE.INDX, MARKET.CN].get_date_range('000001.XSHG')
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

    def get_yield_curve(self, start_date, end_date, tenor=None):
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor=tenor)

    @lru_cache(1024)
    def get_futures_trading_parameters(self, instrument: Instrument, dt: datetime) -> FuturesTradingParameters:
        return self._future_info_store.get_future_info(instrument.order_book_id, instrument.underlying_symbol)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        raise NotImplementedError

    def history_ticks(self, instrument, count, dt):
        raise NotImplementedError

    def get_algo_bar(self, id_or_ins: Union[str, Instrument], start_min: int, end_min: int, dt: datetime) -> Optional[np.ndarray]:
        raise NotImplementedError("open source rqalpha not support algo order")

    def get_open_auction_volume(self, instrument: Instrument, dt: datetime):
        volume = self.get_open_auction_bar(instrument, dt)['volume']
        return volume

    # deprecated
    def register_instruments_store(self, instruments_store, market: MARKET = MARKET.CN):
        system_log.warn("register_instruments_store is deprecated, please use register_instruments instead")
        self.register_instruments(instruments_store.get_instruments(None))

    exchange_rate_1 = ExchangeRate(
        bid_reference=1,
        ask_reference=1,
        bid_settlement_sh=1,
        ask_settlement_sh=1,
        bid_settlement_sz=1,
        ask_settlement_sz=1
    )

    def get_exchange_rate(self, trading_date: date, local: MARKET, settlement: MARKET = MARKET.CN) -> ExchangeRate:
        if local == settlement:
            return self.exchange_rate_1
        else:
            raise NotImplementedError