from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from rqalpha.const import TRADING_CALENDAR_TYPE
from rqalpha.data.bundle import AutomaticUpdateBundle
from rqalpha.data.trading_dates_mixin import TradingDatesMixin
from rqalpha.environment import Environment
from rqalpha.interface import AbstractDataSource
from rqalpha.utils.testing import mock_instrument


@pytest.fixture(params=["ns", "us"])
def trading_dates(request):
    """构造两种精度的交易日历，让每个用例都覆盖纳秒和微秒日期比较"""
    calendar = pd.DatetimeIndex(["2005-01-03", "2005-01-04", "2005-01-05", "2010-03-31", "2010-04-01", "2010-04-02"])
    if hasattr(calendar, "as_unit"):
        calendar = calendar.as_unit(request.param)
    elif request.param == "us":
        pytest.skip("Pandas < 2 only supports nanosecond trading calendars")

    data_source = Mock(spec=AbstractDataSource)
    data_source.get_trading_calendars.return_value = {TRADING_CALENDAR_TYPE.CN_STOCK: calendar}
    return TradingDatesMixin(data_source)


@pytest.mark.parametrize(
    "start_date, first_date, next_date",
    [
        pytest.param(None, date(2005, 1, 4), date(2005, 1, 5), id="default-integer"),  # 不传 start_date：验证默认整数 20050104 对应的查询日期是 2005-01-04
        pytest.param(20100401, date(2010, 4, 1), date(2010, 4, 2), id="explicit-integer"),  # 显式传入整数：验证期货参数更新从 2010-04-01 开始查询
        pytest.param(date(2005, 1, 4), date(2005, 1, 4), date(2005, 1, 5), id="date-object"),  # 传入 date 对象：验证原本正确的日期输入仍保持相同的查询范围
    ],
)
def test_bundle_update_uses_calendar_dates(tmp_path, monkeypatch, trading_dates, start_date, first_date, next_date):
    """验证首次和增量更新的实际查询日期、数据保留及已覆盖缓存的复用。"""
    base_config = SimpleNamespace(end_date=first_date)
    env = SimpleNamespace(
        config=SimpleNamespace(base=base_config),
        data_proxy=SimpleNamespace(_data_source=trading_dates),
    )
    monkeypatch.setattr(Environment, "_env", env)
    instrument = mock_instrument("000001.XSHE", listed_date="1991-04-03", symbol="测试股票")
    requested_dates = []
    volumes = {first_date: 100, next_date: 200}

    def get_open_auction_info(order_book_id, start, end, fields):
        # 保留原始参数传入交易日历，验证日期解析结果，不约束转换发生的位置。
        assert fields == ["volume"]
        dates = trading_dates.get_trading_dates(start, end)
        requested_dates.append(list(dates.date))
        timestamps = [datetime.combine(day.date(), time(9)) for day in dates]
        index = pd.MultiIndex.from_product(
            [[order_book_id], timestamps], names=["order_book_id", "datetime"]
        )
        return pd.DataFrame({"volume": [volumes[day.date()] for day in dates]}, index=index)

    def make_bundle():
        kwargs = {} if start_date is None else {"start_date": start_date}
        return AutomaticUpdateBundle(
            path=str(tmp_path),
            filename="open_auction_volume.h5",
            api=get_open_auction_info,
            fields=["volume"],
            end_date=base_config.end_date,
            **kwargs,
        )

    first_record = make_bundle().get_data(instrument, first_date)
    assert first_record is not None
    assert first_record["volume"] == 100
    assert requested_dates == [[first_date]]

    # 用新实例模拟下次回测：从已有缓存的下一交易日开始追加数据。
    base_config.end_date = next_date
    bundle = make_bundle()
    next_record = bundle.get_data(instrument, next_date)
    assert next_record is not None
    assert next_record["volume"] == 200
    previous_record = bundle.get_data(instrument, first_date)
    assert previous_record is not None
    assert previous_record["volume"] == 100
    assert requested_dates == [[first_date], [next_date]]

    cached_record = make_bundle().get_data(instrument, next_date)
    assert cached_record is not None
    assert cached_record["volume"] == 200
    assert len(requested_dates) == 2


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
