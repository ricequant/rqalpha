# -*- coding: utf-8 -*-
import warnings
from datetime import date, datetime

from rqalpha.utils.datetime_func import convert_int_to_datetime
from rqalpha.utils.testing import DataProxyFixture, RQAlphaTestCase


class WeeklyHistoryBarsTestCase(DataProxyFixture, RQAlphaTestCase):
    def test_weekly_history_bars(self):
        instrument = self.data_proxy.instrument("000001.XSHE")
        dt = datetime(2020, 2, 1)

        with warnings.catch_warnings():
            # 把 pandas 3 的别名弃用消息升级为错误（pandas 2 上无此警告，惰性）
            warnings.filterwarnings(
                "error", message=".*is deprecated and will be removed in a future version, please use.*"
            )
            weekly_bars = self.data_proxy.history_bars(instrument, 3, "1w", None, dt, adjust_type="none")
            weekly_close = self.data_proxy.history_bars(instrument, 3, "1w", "close", dt)

        dates = [convert_int_to_datetime(x).date() for x in weekly_bars["datetime"]]
        assert len(weekly_bars) == 3
        assert dates == [date(2020, 1, 10), date(2020, 1, 17), date(2020, 1, 23)]

        daily_close = self.data_proxy.history_bars(instrument, 20, "1d", "close", dt)
        assert weekly_close[-1] == daily_close[-1]
