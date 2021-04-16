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

import six
from datetime import datetime
import numpy as np

from rqalpha.core.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.const import RUN_TYPE
from rqalpha.utils.datetime_func import convert_int_to_datetime
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import system_log
from rqalpha.utils.exception import patch_user_exc
from rqalpha.utils.repr import PropertyReprMeta
from rqalpha.utils.class_helper import cached_property
from rqalpha.const import EXECUTION_PHASE

NAMES = ['open', 'close', 'low', 'high', 'settlement', 'limit_up', 'limit_down', 'volume', 'total_turnover',
         'discount_rate', 'acc_net_value', 'unit_net_value', 'open_interest',
         'basis_spread', 'prev_settlement', 'datetime']
NANDict = {i: np.nan for i in NAMES}


class PartialBarObject(metaclass=PropertyReprMeta):
    # 用于 open_auction
    __repr_properties__ = (
        "order_book_id", "datetime", "open", "limit_up", "limit_down"
    )

    def __init__(self, instrument, data, dt=None):
        self._dt = dt
        self._data = data if data is not None else NANDict
        self._instrument = instrument
        self._env = Environment.get_instance()

    @cached_property
    def datetime(self):
        """
        [datetime.datetime] 时间戳
        """
        if self._dt is not None:
            return self._dt
        dt = self._data["datetime"]
        if isinstance(dt, datetime):
            return dt
        return convert_int_to_datetime(dt)

    @cached_property
    def instrument(self):
        return self._instrument

    @cached_property
    def order_book_id(self):
        """
        [str] 交易标的代码
        """
        return self._instrument.order_book_id

    @cached_property
    def symbol(self):
        """
        [str] 合约简称
        """
        return self._instrument.symbol

    @cached_property
    def open(self):
        """
        [float] 开盘价
        """
        return self._data["open"]

    @cached_property
    def limit_up(self):
        """
        [float] 涨停价
        """
        try:
            v = self._data['limit_up']
            return v if v != 0 else np.nan
        except (KeyError, ValueError):
            return np.nan

    @cached_property
    def limit_down(self):
        """
        [float] 跌停价
        """
        try:
            v = self._data['limit_down']
            return v if v != 0 else np.nan
        except (KeyError, ValueError):
            return np.nan

    @cached_property
    def last(self):
        """
        [float] 当前最新价
        """
        try:
            return self._data["last"]
        except KeyError:
            return self.open

    @cached_property
    def volume(self):
        """
        [float] 截止到当前的成交量
        """
        return self._data["volume"]

    @cached_property
    def total_turnover(self):
        """
        [float] 截止到当前的成交额
        """
        return self._data['total_turnover']

    @cached_property
    def prev_close(self):
        """
        [float] 昨日收盘价
        """
        try:
            return self._data['prev_close']
        except (ValueError, KeyError):
            return self._env.data_proxy.get_prev_close(self._instrument.order_book_id, self._env.trading_dt)

    @cached_property
    def prev_settlement(self):
        """
        [float] 昨日结算价（期货专用）
        """
        try:
            return self._data['prev_settlement']
        except (ValueError, KeyError):
            return self._env.data_proxy.get_prev_settlement(self._instrument.order_book_id, self._env.trading_dt)

    @cached_property
    def isnan(self):
        return np.isnan(self._data['close'])


class BarObject(PartialBarObject):
    __repr_properties__ = (
        "order_book_id", "datetime", "open", "close", "high", "low", "limit_up", "limit_down"
    )

    @cached_property
    def close(self):
        """
        [float] 收盘价
        """
        return self._data["close"]

    @cached_property
    def low(self):
        """
        [float] 最低价
        """
        return self._data["low"]

    @cached_property
    def high(self):
        """
        [float] 最高价
        """
        return self._data["high"]

    @cached_property
    def last(self):
        """
        [float] 当前最新价
        """
        return self.close

    @cached_property
    def discount_rate(self):
        return self._data['discount_rate']

    @cached_property
    def acc_net_value(self):
        return self._data['acc_net_value']

    @cached_property
    def unit_net_value(self):
        return self._data['unit_net_value']

    INDEX_MAP = {
        'IF': '000300.XSHG',
        'IH': '000016.XSHG',
        'IC': '000905.XSHG',
    }

    @cached_property
    def basis_spread(self):
        try:
            return self._data['basis_spread']
        except (ValueError, KeyError):
            if self._instrument.type != 'Future' or Environment.get_instance().config.base.run_type != RUN_TYPE.PAPER_TRADING:
                raise
            if self._instrument.underlying_symbol in ['IH', 'IC', 'IF']:
                order_book_id = self.INDEX_MAP[self._instrument.underlying_symbol]
                bar = Environment.get_instance().data_proxy.get_bar(order_book_id, None, '1m')
                return self.close - bar.close
            else:
                return np.nan

    @cached_property
    def settlement(self):
        """
        [float] 结算价（期货专用）
        """
        return self._data['settlement']

    @cached_property
    def open_interest(self):
        """
        [float] 截止到当前的持仓量（期货专用）
        """
        return self._data['open_interest']

    @cached_property
    def is_trading(self):
        """
        [bool] 是否有成交量
        """
        return self._data['volume'] > 0

    @cached_property
    def isnan(self):
        return np.isnan(self._data['close'])

    @cached_property
    def suspended(self):
        if self.isnan:
            return True

        return Environment.get_instance().data_proxy.is_suspended(self._instrument.order_book_id, int(self._data['datetime'] // 1000000))

    def mavg(self, intervals, frequency='1d'):
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        env = Environment.get_instance()
        dt = env.calendar_dt

        if (env.config.base.frequency == '1m' and frequency == '1d') or ExecutionContext.phase() == EXECUTION_PHASE.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = env.data_proxy.get_previous_trading_date(env.calendar_dt.date())
        bars = env.data_proxy.fast_history(self._instrument.order_book_id, intervals, frequency, 'close', dt)
        return bars.mean()

    def vwap(self, intervals, frequency='1d'):
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        env = Environment.get_instance()
        dt = env.calendar_dt

        if (env.config.base.frequency == '1m' and frequency == '1d') or ExecutionContext.phase() == EXECUTION_PHASE.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = env.data_proxy.get_previous_trading_date(env.calendar_dt.date())
        bars = env.data_proxy.fast_history(self._instrument.order_book_id, intervals, frequency, ['close', 'volume'], dt)
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
            base.extend((k, v) for k, v in self._data.items() if k != 'datetime')
        else:
            base.extend((n, self._data[n]) for n in self._data.dtype.names if n != 'datetime')
        return "Bar({0})".format(', '.join('{0}: {1}'.format(k, v) for k, v in base))

    def __getitem__(self, key):
        return self.__dict__[key]

    def __getattr__(self, item):
        try:
            value = self._data[item]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))
        else:
            if isinstance(value, bytes):
                return value.decode("utf-8")
            return value


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
        return ((o, self.__getitem__(o)) for o in Environment.get_instance().get_universe())

    def keys(self):
        return (o for o in Environment.get_instance().get_universe())

    def values(self):
        return (self.__getitem__(o) for o in Environment.get_instance().get_universe())

    def __contains__(self, o):
        return o in Environment.get_instance().get_universe()

    def __len__(self):
        return len(Environment.get_instance().get_universe())

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
                if not self._dt:
                    return BarObject(instrument, NANDict, self._dt)
                if ExecutionContext.phase() == EXECUTION_PHASE.OPEN_AUCTION:
                    bar = self._data_proxy.get_open_auction_bar(order_book_id, self._dt)
                else:
                    bar = self._data_proxy.get_bar(order_book_id, self._dt, self._frequency)
            except PermissionError:
                raise
            except Exception as e:
                system_log.exception(e)
                raise patch_user_exc(KeyError(_(u"id_or_symbols {} does not exist").format(key)))
            if bar is None:
                return BarObject(instrument, NANDict, self._dt)
            else:
                self._cache[order_book_id] = bar
                return bar

    @cached_property
    def dt(self):
        return self._dt

    def __repr__(self):
        keys = list(self.keys())
        s = ', '.join(keys[:10]) + (' ...' if len(keys) > 10 else '')
        return "{}({})".format(type(self).__name__, s)
