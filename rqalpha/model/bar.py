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

import six
import numpy as np

from ..environment import Environment
from ..const import RUN_TYPE
from ..utils.datetime_func import convert_int_to_datetime
from ..utils.i18n import gettext as _
from ..utils.logger import system_log
from ..utils.exception import patch_user_exc
from ..execution_context import ExecutionContext
from ..const import EXECUTION_PHASE, BAR_STATUS


NAMES = ['open', 'close', 'low', 'high', 'settlement', 'limit_up', 'limit_down', 'volume', 'total_turnover',
         'discount_rate', 'acc_net_value', 'unit_net_value', 'open_interest',
         'basis_spread', 'prev_settlement', 'datetime']
NANDict = {i: np.nan for i in NAMES}


class BarObject(object):
    def __init__(self, instrument, data, dt=None):
        self._dt = dt
        self._data = data if data is not None else NANDict
        self._prev_close = None
        self._prev_settlement = None
        self._basis_spread = None
        self._limit_up = None
        self._limit_down = None
        self.__internal_limit_up = None
        self.__internal_limit_down = None
        self._instrument = instrument

    @property
    def open(self):
        """
        【float】当日开盘价
        """
        return self._data["open"]

    @property
    def close(self):
        return self._data["close"]

    @property
    def low(self):
        """
        【float】截止到当前的最低价
        """
        return self._data["low"]

    @property
    def high(self):
        """
        【float】截止到当前的最高价
        """
        return self._data["high"]

    @property
    def limit_up(self):
        try:
            v = self._data['limit_up']
            return v if v != 0 else np.nan
        except (ValueError, KeyError):
            if self._limit_up is None:
                data_proxy = ExecutionContext.data_proxy
                dt = ExecutionContext.get_current_trading_dt()
                if data_proxy.is_st_stock(self._instrument.order_book_id, dt):
                    self._limit_up = np.floor(self.prev_close * 10500) / 10000
                else:
                    self._limit_up = np.floor(self.prev_close * 11000) / 10000
            return self._limit_up

    @property
    def limit_down(self):
        try:
            v = self._data['limit_down']
            return v if v != 0 else np.nan
        except (ValueError, KeyError):
            if self._limit_down is None:
                data_proxy = ExecutionContext.data_proxy
                dt = ExecutionContext.get_current_trading_dt()
                if data_proxy.is_st_stock(self._instrument.order_book_id, dt):
                    self._limit_down = np.ceil(self.prev_close * 9500) / 10000
                else:
                    self._limit_down = np.ceil(self.prev_close * 9000) / 10000
            return self._limit_down

    @property
    def _internal_limit_up(self):
        try:
            v = self._data['limit_up']
            return v if v != 0 else np.nan
        except (ValueError, KeyError):
            if self.__internal_limit_up is None:
                data_proxy = ExecutionContext.data_proxy
                dt = ExecutionContext.get_current_trading_dt()
                if data_proxy.is_st_stock(self._instrument.order_book_id, dt):
                    self.__internal_limit_up = np.floor(self.prev_close * 10490) / 10000
                else:
                    self.__internal_limit_up = np.floor(self.prev_close * 10990) / 10000
            return self.__internal_limit_up

    @property
    def _internal_limit_down(self):
        try:
            v = self._data['limit_down']
            return v if v != 0 else np.nan
        except (ValueError, KeyError):
            if self.__internal_limit_down is None:
                data_proxy = ExecutionContext.data_proxy
                dt = ExecutionContext.get_current_trading_dt()
                if data_proxy.is_st_stock(self._instrument.order_book_id, dt):
                    self.__internal_limit_down = np.ceil(self.prev_close * 9510) / 10000
                else:
                    self.__internal_limit_down = np.ceil(self.prev_close * 9010) / 10000
            return self.__internal_limit_down

    @property
    def prev_close(self):
        """
        【float】截止到当前的最低价
        """
        try:
            return self._data['prev_close']
        except (ValueError, KeyError):
            pass

        if self._prev_close is None:
            data_proxy = ExecutionContext.data_proxy
            dt = ExecutionContext.get_current_trading_dt()
            self._prev_close = data_proxy.get_prev_close(self._instrument.order_book_id, dt)
        return self._prev_close

    @property
    def _bar_status(self):
        """
        WARNING: 获取 bar_status 比较耗费性能，而且是lazy_compute，因此不要多次调用！！！！
        """
        if self.isnan or np.isnan(self.limit_up):
            return BAR_STATUS.ERROR
        if self.close >= self._internal_limit_up:
            return BAR_STATUS.LIMIT_UP
        if self.close <= self._internal_limit_down:
            return BAR_STATUS.LIMIT_DOWN
        return BAR_STATUS.NORMAL

    @property
    def last(self):
        """
        【float】当前最新价
        """
        return self.close

    @property
    def volume(self):
        """
        【float】截止到当前的成交量
        """
        return self._data["volume"]

    @property
    def total_turnover(self):
        """
        【float】截止到当前的成交额
        """
        return self._data['total_turnover']

    @property
    def discount_rate(self):
        return self._data['discount_rate']

    @property
    def acc_net_value(self):
        return self._data['acc_net_value']

    @property
    def unit_net_value(self):
        return self._data['unit_net_value']

    INDEX_MAP = {
        'IF': '000300.XSHG',
        'IH': '000016.XSHG',
        'IC': '000905.XSHG',
    }

    @property
    def basis_spread(self):
        try:
            return self._data['basis_spread']
        except (ValueError, KeyError):
            if self._instrument.type != 'Future' or ExecutionContext.config.base.run_type != RUN_TYPE.PAPER_TRADING:
                raise

        if self._basis_spread is None:
            if self._instrument.underlying_symbol in ['IH', 'IC', 'IF']:
                order_book_id = self.INDEX_MAP[self._instrument.underlying_symbol]
                bar = ExecutionContext.data_proxy.get_bar(order_book_id, None, '1m')
                self._basis_spread = self.close - bar.close
            else:
                self._basis_spread = np.nan
        return self._basis_spread

    @property
    def settlement(self):
        return self._data['settlement']

    @property
    def prev_settlement(self):
        """
        【float】昨日结算价（期货专用）
        """
        try:
            return self._data['prev_settlement']
        except (ValueError, KeyError):
            pass

        if self._prev_settlement is None:
            data_proxy = ExecutionContext.data_proxy
            dt = ExecutionContext.get_current_trading_dt().date()
            self._prev_settlement = data_proxy.get_prev_settlement(self._instrument.order_book_id, dt)
        return self._prev_settlement

    @property
    def open_interest(self):
        """
        【float】截止到当前的持仓量（期货专用）
        """
        return self._data['open_interest']

    @property
    def datetime(self):
        if self._dt is not None:
            return self._dt
        return convert_int_to_datetime(self._data['datetime'])

    @property
    def instrument(self):
        return self._instrument

    @property
    def order_book_id(self):
        """
        【str】交易标的代码
        """
        return self._instrument.order_book_id

    @property
    def symbol(self):
        """
        【str】合约简称
        """
        return self._instrument.symbol

    @property
    def is_trading(self):
        """
        【datetime.datetime】 时间戳
        """
        return self._data['volume'] > 0

    @property
    def isnan(self):
        return np.isnan(self._data['close'])

    @property
    def suspended(self):
        if self.isnan:
            return True

        data_proxy = ExecutionContext.data_proxy
        return data_proxy.is_suspended(self._instrument.order_book_id, int(self._data['datetime'] // 1000000))

    def mavg(self, intervals, frequency='1d'):
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        dt = ExecutionContext.get_current_calendar_dt()
        data_proxy = ExecutionContext.data_proxy

        if (Environment.get_instance().config.base.frequency == '1m' and frequency == '1d') or \
                        ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = data_proxy.get_previous_trading_date(dt.date())
        bars = data_proxy.fast_history(self._instrument.order_book_id, intervals, frequency, 'close', dt)
        return bars.mean()

    def vwap(self, intervals, frequency='1d'):
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        dt = ExecutionContext.get_current_calendar_dt()
        data_proxy = ExecutionContext.data_proxy

        if (Environment.get_instance().config.base.frequency == '1m' and frequency == '1d') or \
                        ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = data_proxy.get_previous_trading_date(dt.date())
        bars = data_proxy.fast_history(self._instrument.order_book_id, intervals, frequency, ['close', 'volume'], dt)
        sum = bars['volume'].sum()
        if sum == 0:
            # 全部停牌
            return 0

        return np.dot(bars['close'], bars['volume']) / sum

    def __repr__(self):
        base = [
            ('symbol', repr(self._instrument.symbol)),
            ('order_book_id', repr(self._instrument.order_book_id)),
            ('datetime', repr(self.datetime)),
        ]

        if self.isnan:
            base.append(('error', repr('DATA UNAVAILABLE')))
            return 'Bar({0})'.format(', '.join('{0}: {1}'.format(k, v) for k, v in base) + ' NaN BAR')

        if isinstance(self._data, dict):
            # in pt
            base.extend((k, v) for k, v in six.iteritems(self._data) if k != 'datetime')
        else:
            base.extend((n, self._data[n]) for n in self._data.dtype.names if n != 'datetime')
        return "Bar({0})".format(', '.join('{0}: {1}'.format(k, v) for k, v in base))

    def __getitem__(self, key):
        return self.__dict__[key]


class BarMap(object):
    def __init__(self, data_proxy, frequency):
        self._dt = None
        self._data_proxy = data_proxy
        self._frequency = frequency
        self._cache = {}

    def update_dt(self, dt):
        self._dt = dt
        self._cache.clear()

    def items(self):
        return ((o, self.__getitem__(o)) for o in Environment.get_instance().universe)

    def keys(self):
        return (o for o in Environment.get_instance().universe)

    def values(self):
        return (self.__getitem__(o) for o in Environment.get_instance().universe)

    def __contains__(self, o):
        return o in Environment.get_instance().universe

    def __len__(self):
        return len(Environment.get_instance().universe)

    def __getitem__(self, key):
        if not isinstance(key, six.string_types):
            raise patch_user_exc(ValueError('invalid key {} (use order_book_id please)'.format(key)))

        instrument = self._data_proxy.instruments(key)
        if instrument is None:
            raise patch_user_exc(ValueError('invalid order book id or symbol: {}'.format(key)))
        order_book_id = instrument.order_book_id

        try:
            return self._cache[order_book_id]
        except KeyError:
            try:
                bar = self._data_proxy.get_bar(order_book_id, self._dt, self._frequency)
            except Exception as e:
                system_log.exception(e)
                raise patch_user_exc(KeyError(_("id_or_symbols {} does not exist").format(key)))
            if bar is None:
                return BarObject(instrument, NANDict, self._dt)
            else:
                self._cache[order_book_id] = bar
                return bar

    @property
    def dt(self):
        return self._dt

    def __repr__(self):
        keys = list(self.keys())
        s = ', '.join(keys[:10]) + (' ...' if len(keys) > 10 else '')
        return "{}({})".format(type(self).__name__, s)
