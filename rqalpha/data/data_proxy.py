# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
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

import re
from datetime import datetime, date
from typing import Union, List, Sequence, Optional, Iterable

import six
import numpy as np
import pandas as pd

from rqalpha.const import INSTRUMENT_TYPE, TRADING_CALENDAR_TYPE
from rqalpha.utils import risk_free_helper, TimeRange, merge_trading_period
from rqalpha.data.trading_dates_mixin import TradingDatesMixin
from rqalpha.model.bar import BarObject, NANDict, PartialBarObject
from rqalpha.model.tick import TickObject
from rqalpha.model.instrument import Instrument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.datetime_func import convert_int_to_datetime, convert_date_to_int
from rqalpha.utils.typing import DateLike, StrOrIter
from rqalpha.interface import AbstractDataSource, AbstractPriceBoard


class DataProxy(TradingDatesMixin):
    def __init__(self, data_source, price_board):
        # type: (AbstractDataSource, AbstractPriceBoard) -> None
        self._data_source = data_source
        self._price_board = price_board
        try:
            trading_calendars = data_source.get_trading_calendars()
        except NotImplementedError:
            # forward compatible
            trading_calendars = {TRADING_CALENDAR_TYPE.EXCHANGE: data_source.get_trading_calendar()}
        TradingDatesMixin.__init__(self, trading_calendars)

    def __getattr__(self, item):
        return getattr(self._data_source, item)

    def get_trading_minutes_for(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        minutes = self._data_source.get_trading_minutes_for(instrument, dt)
        return [] if minutes is None else minutes

    def get_yield_curve(self, start_date, end_date, tenor=None):
        if isinstance(tenor, six.string_types):
            tenor = [tenor]
        return self._data_source.get_yield_curve(start_date, end_date, tenor)

    def get_risk_free_rate(self, start_date, end_date):
        tenor = risk_free_helper.get_tenor_for(start_date, end_date)
        yc = self._data_source.get_yield_curve(start_date, start_date, [tenor])
        if yc is None or yc.empty:
            return 0
        rate = yc.values[0, 0]
        return 0 if np.isnan(rate) else rate

    def get_dividend(self, order_book_id):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_dividend(instrument)

    def get_split(self, order_book_id):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_split(instrument)

    def get_dividend_by_book_date(self, order_book_id, date):
        table = self._data_source.get_dividend(self.instruments(order_book_id))
        if table is None or len(table) == 0:
            return

        try:
            dates = table['book_closure_date']
        except ValueError:
            dates = table['ex_dividend_date']
            date = self.get_next_trading_date(date)

        dt = date.year * 10000 + date.month * 100 + date.day

        left_pos = dates.searchsorted(dt)
        right_pos = dates.searchsorted(dt, side="right")

        if left_pos >= right_pos:
            return None

        return table[left_pos: right_pos]

    def get_split_by_ex_date(self, order_book_id, date):
        df = self.get_split(order_book_id)
        if df is None or len(df) == 0:
            return

        dt = convert_date_to_int(date)
        pos = df['ex_date'].searchsorted(dt)
        if pos == len(df) or df['ex_date'][pos] != dt:
            return None

        return df['split_factor'][pos]

    @lru_cache(10240)
    def _get_prev_close(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'close', prev_trading_date,
                                             skip_suspended=False, include_now=False, adjust_orig=dt)
        if bar is None or len(bar) < 1:
            return np.nan
        return bar[0]

    def get_prev_close(self, order_book_id, dt):
        return self._get_prev_close(order_book_id, dt.replace(hour=0, minute=0, second=0))

    @lru_cache(10240)
    def _get_prev_settlement(self, instrument, dt):
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'settlement', prev_trading_date,
                                             skip_suspended=False, adjust_orig=dt)
        if bar is None or len(bar) == 0:
            return np.nan
        return bar[0]

    @lru_cache(10240)
    def _get_settlement(self, instrument, dt):
        bar = self._data_source.history_bars(instrument, 1, '1d', 'settlement', dt, skip_suspended=False)
        if bar is None or len(bar) == 0:
            raise LookupError("'{}', dt={}".format(instrument.order_book_id, dt))
        return bar[0]

    def get_prev_settlement(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        if instrument.type not in (INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.OPTION):
            return np.nan
        return self._get_prev_settlement(instrument, dt)

    def get_settlement(self, instrument, dt):
        # type: (Instrument, datetime) -> float
        if instrument.type != INSTRUMENT_TYPE.FUTURE:
            raise LookupError("'{}', instrument_type={}".format(instrument.order_book_id, instrument.type))
        return self._get_settlement(instrument, dt)

    def get_settle_price(self, order_book_id, date):
        instrument = self.instruments(order_book_id)
        if instrument.type != 'Future':
            return np.nan
        return self._data_source.get_settle_price(instrument, date)

    @lru_cache(512)
    def get_bar(self, order_book_id, dt, frequency='1d'):
        # type: (str, Union[datetime, date], str) -> BarObject
        instrument = self.instruments(order_book_id)
        if dt is None:
            return BarObject(instrument, NANDict, dt)
        bar = self._data_source.get_bar(instrument, dt, frequency)
        if bar:
            return BarObject(instrument, bar)
        return BarObject(instrument, NANDict, dt)

    def get_open_auction_bar(self, order_book_id, dt):
        return PartialBarObject(self.current_snapshot(order_book_id, "1d", dt))

    def history(self, order_book_id, bar_count, frequency, field, dt):
        data = self.history_bars(order_book_id, bar_count, frequency,
                                 ['datetime', field], dt, skip_suspended=False, adjust_orig=dt)
        if data is None:
            return None
        return pd.Series(data[field], index=[convert_int_to_datetime(t) for t in data['datetime']])

    def fast_history(self, order_book_id, bar_count, frequency, field, dt):
        return self.history_bars(order_book_id, bar_count, frequency, field, dt, skip_suspended=False,
                                 adjust_type='pre', adjust_orig=dt)

    def history_bars(self, order_book_id, bar_count, frequency, field, dt,
                     skip_suspended=True, include_now=False,
                     adjust_type='pre', adjust_orig=None):
        instrument = self.instruments(order_book_id)
        if adjust_orig is None:
            adjust_orig = dt
        return self._data_source.history_bars(instrument, bar_count, frequency, field, dt,
                                              skip_suspended=skip_suspended, include_now=include_now,
                                              adjust_type=adjust_type, adjust_orig=adjust_orig)

    def history_ticks(self, order_book_id, count, dt):
        instrument = self.instruments(order_book_id)
        return self._data_source.history_ticks(instrument, count, dt)

    def current_snapshot(self, order_book_id, frequency, dt):

        def tick_fields_for(ins):
            _STOCK_FIELD_NAMES = [
                'datetime', 'open', 'high', 'low', 'last', 'volume', 'total_turnover', 'prev_close',
                'limit_up', 'limit_down'
            ]
            _FUTURE_FIELD_NAMES = _STOCK_FIELD_NAMES + ['open_interest', 'prev_settlement']

            if ins.type == 'Future':
                return _STOCK_FIELD_NAMES
            else:
                return _FUTURE_FIELD_NAMES

        instrument = self.instruments(order_book_id)
        if frequency == '1d':
            bar = self._data_source.get_bar(instrument, dt, '1d')
            if not bar:
                return None
            d = {k: bar[k] for k in tick_fields_for(instrument) if k in bar.dtype.names}
            d['last'] = bar['close']
            d['prev_close'] = self._get_prev_close(order_book_id, dt)
            return TickObject(instrument, d)

        return self._data_source.current_snapshot(instrument, frequency, dt)

    def available_data_range(self, frequency):
        return self._data_source.available_data_range(frequency)

    def get_commission_info(self, order_book_id):
        instrument = self.instruments(order_book_id)
        return self._data_source.get_commission_info(instrument)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        return self._data_source.get_merge_ticks(order_book_id_list, trading_date, last_dt)

    def is_suspended(self, order_book_id, dt, count=1):
        # type: (str, DateLike, int) -> Union[Sequence[bool], bool]
        if count == 1:
            return self._data_source.is_suspended(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.is_suspended(order_book_id, trading_dates)

    def is_st_stock(self, order_book_id, dt, count=1):
        if count == 1:
            return self._data_source.is_st_stock(order_book_id, [dt])[0]

        trading_dates = self.get_n_trading_dates_until(dt, count)
        return self._data_source.is_st_stock(order_book_id, trading_dates)

    def get_tick_size(self, order_book_id):
        return self.instruments(order_book_id).tick_size()

    def get_last_price(self, order_book_id):
        # type: (str) -> float
        return float(self._price_board.get_last_price(order_book_id))

    def all_instruments(self, types, dt=None):
        # type: (List[INSTRUMENT_TYPE], Optional[datetime]) -> List[Instrument]
        return [i for i in self._data_source.get_instruments(types=types) if dt is None or i.listing_at(dt)]

    def instruments(self, sym_or_ids):
        # type: (StrOrIter) -> Union[None, Instrument, List[Instrument]]
        if isinstance(sym_or_ids, str):
            return next(iter(self._data_source.get_instruments(id_or_syms=[sym_or_ids])), None)
        else:
            return list(self._data_source.get_instruments(id_or_syms=sym_or_ids))

    FUTURE_CONTINUOUS_CONTRACT = re.compile("^[A-Z]{1,2}(88|888|99|889)$")

    def get_future_contracts(self, underlying, date):
        # type: (str, DateLike) -> List[str]
        return sorted(i.order_book_id for i in self.all_instruments(
            [INSTRUMENT_TYPE.FUTURE], date
        ) if i.underlying_symbol == underlying and not re.match(self.FUTURE_CONTINUOUS_CONTRACT, i.order_book_id))

    def get_trading_period(self, sym_or_ids, default_trading_period=None):
        # type: (StrOrIter, Optional[Sequence[TimeRange]]) -> List[TimeRange]
        trading_period = default_trading_period or []
        for instrument in self.instruments(sym_or_ids):
            trading_period.extend(instrument.trading_hours or [])
        return merge_trading_period(trading_period)

    def is_night_trading(self, sym_or_ids):
        # type: (StrOrIter) -> bool
        return any((instrument.trade_at_night for instrument in self.instruments(sym_or_ids)))
