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

import datetime
from typing import Dict

import pandas as pd

from rqalpha.utils.functools import lru_cache
from rqalpha.const import TRADING_CALENDAR_TYPE


def _to_timestamp(d):
    return pd.Timestamp(d).replace(hour=0, minute=0, second=0, microsecond=0)


class TradingDatesMixin(object):
    def __init__(self, trading_calendars):
        # type: (Dict[TRADING_CALENDAR_TYPE, pd.DatetimeIndex]) -> TradingDatesMixin
        self.trading_calendars = trading_calendars
        self.merged_trading_calendars = pd.DatetimeIndex(sorted(set.union(*(
            set(calendar) for calendar in trading_calendars.values()
        ))))

    def get_trading_calendar(self, trading_calendar_type=None):
        if trading_calendar_type is None:
            return self.merged_trading_calendars
        try:
            return self.trading_calendars[trading_calendar_type]
        except KeyError:
            raise NotImplementedError("unsupported trading_calendar_type {}".format(trading_calendar_type))

    def get_trading_dates(self, start_date, end_date, trading_calendar_type=None):
        # 只需要date部分
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        start_date = _to_timestamp(start_date)
        end_date = _to_timestamp(end_date)
        left = trading_dates.searchsorted(start_date)
        right = trading_dates.searchsorted(end_date, side='right')
        return trading_dates[left:right]

    def get_previous_trading_date(self, date, n=1, trading_calendar_type=None):
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        pos = trading_dates.searchsorted(_to_timestamp(date))
        if pos >= n:
            return trading_dates[pos - n]
        else:
            return trading_dates[0]

    def get_next_trading_date(self, date, n=1, trading_calendar_type=None):
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        pos = trading_dates.searchsorted(_to_timestamp(date), side='right')
        if pos + n > len(trading_dates):
            return trading_dates[-1]
        else:
            return trading_dates[pos + n - 1]

    def is_trading_date(self, date, trading_calendar_type=None):
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        pos = trading_dates.searchsorted(_to_timestamp(date))
        return pos < len(trading_dates) and trading_dates[pos] == date

    def get_future_trading_date(self, dt):
        return self._get_future_trading_date(dt.replace(minute=0, second=0, microsecond=0))

    def get_n_trading_dates_until(self, dt, n, trading_calendar_type=None):
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        pos = trading_dates.searchsorted(_to_timestamp(dt), side='right')
        if pos >= n:
            return trading_dates[pos - n:pos]

        return trading_dates[:pos]

    def count_trading_dates(self, start_date, end_date, trading_calendar_type=None):
        start_date = _to_timestamp(start_date)
        end_date = _to_timestamp(end_date)
        trading_dates = self.get_trading_calendar(trading_calendar_type)
        return trading_dates.searchsorted(end_date, side='right') - trading_dates.searchsorted(start_date)

    @lru_cache(512)
    def _get_future_trading_date(self, dt):
        dt1 = dt - datetime.timedelta(hours=4)
        td = pd.Timestamp(dt1.date())
        trading_dates = self.get_trading_calendar(TRADING_CALENDAR_TYPE.EXCHANGE)
        pos = trading_dates.searchsorted(td)
        if trading_dates[pos] != td:
            raise RuntimeError('invalid future calendar datetime: {}'.format(dt))
        if dt1.hour >= 16:
            return trading_dates[pos + 1]

        return td
