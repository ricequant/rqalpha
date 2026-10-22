# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

from datetime import date, datetime
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from rqalpha.const import TRADING_CALENDAR_TYPE
from rqalpha.data.trading_dates_mixin import TradingDatesMixin
from rqalpha.interface import AbstractDataSource
from rqalpha.utils.testing import DataProxyFixture, RQAlphaTestCase


class TradingDateMixinTestCase(DataProxyFixture, RQAlphaTestCase):
    def init_fixture(self):
        super(TradingDateMixinTestCase, self).init_fixture()

    def test_count_trading_dates(self):
        assert self.data_proxy.count_trading_dates(date(2018, 11, 1), date(2018, 11, 12)) == 8
        assert self.data_proxy.count_trading_dates(date(2018, 11, 3), date(2018, 11, 12)) == 6
        assert self.data_proxy.count_trading_dates(date(2018, 11, 3), date(2018, 11, 18)) == 10


@pytest.fixture(params=["ns", "us"])
def trading_dates(request):
    """构造两种精度的交易日历，让每个用例都覆盖纳秒和微秒日期比较"""
    calendar = pd.DatetimeIndex(["2005-01-03", "2005-01-04", "2005-01-05"])
    if hasattr(calendar, "as_unit"):
        calendar = calendar.as_unit(request.param)
    elif request.param == "us":
        pytest.skip("Pandas < 2 only supports nanosecond trading calendars")

    data_source = Mock(spec=AbstractDataSource)
    data_source.get_trading_calendars.return_value = {TRADING_CALENDAR_TYPE.CN_STOCK: calendar}
    return TradingDatesMixin(data_source)


@pytest.mark.parametrize(
    "query_date",
    [
        pytest.param(20050104, id="integer"),  # Python 整数按 YYYYMMDD 解析。
        pytest.param(20050104.0, id="float"),  # 浮点日期编码与整数表示同一天。
        pytest.param(np.int64(20050104), id="numpy-integer"),  # 覆盖 np.integer 分支。
        pytest.param(np.float32(20050104), id="numpy-float"),  # float32 不属于内置 float，覆盖 np.floating 分支。
        pytest.param("2005-01-04", id="string"),  # 保持字符串日期的兼容性。
        pytest.param(date(2005, 1, 4), id="date-object"),  # 保持 date 对象的兼容性。
        pytest.param(datetime(2005, 1, 4, 12, 34, 56), id="datetime"),  # 忽略时分秒。
        pytest.param(pd.Timestamp("2005-01-04 12:34:56.123456104"), id="nanoseconds"),  # 归零时也清除纳秒。
    ],
)
def test_trading_date_queries_normalize_dates(trading_dates, query_date):
    """验证不同日期输入在区间、计数、前后交易日及回溯查询中得到一致结果。"""
    assert list(trading_dates.get_trading_dates(query_date, query_date).date) == [date(2005, 1, 4)]
    assert trading_dates.count_trading_dates(query_date, query_date) == 1
    assert trading_dates.get_previous_trading_date(query_date).date() == date(2005, 1, 3)
    assert trading_dates.get_next_trading_date(query_date).date() == date(2005, 1, 5)
    assert list(trading_dates.get_n_trading_dates_until(query_date, 2).date) == [date(2005, 1, 3), date(2005, 1, 4)]
