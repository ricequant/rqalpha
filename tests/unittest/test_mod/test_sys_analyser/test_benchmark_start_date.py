"""验证 benchmark 通过日期范围 Hook 限制回测起始日，并保留计算首日收益所需的前一日行情。

使用合成行情和真实的 DataProxy、HookRegistry、EventBus 验证日期调整及基准收益计算。
"""

import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from rqalpha.const import TRADING_CALENDAR_TYPE
from rqalpha.core.events import EVENT, Event, EventBus
from rqalpha.core.hooks import HookRegistry
from rqalpha.data.data_proxy import DataProxy
from rqalpha.interface import AbstractDataSource
from rqalpha.main import AVAILABLE_DATA_RANGE, _adjust_start_date
from rqalpha.mod.rqalpha_mod_sys_analyser import __config__, mod as analyser_module
from rqalpha.utils import RqAttrDict
from rqalpha.utils.datetime_func import convert_date_to_int
from rqalpha.utils.exception import InstrumentNotFound
from rqalpha.utils.testing import mock_instrument


@pytest.fixture
def start_analyser(monkeypatch):
    """构造两个数据首日不同的基准，并按框架启动顺序初始化 analyser。

    000300 的数据从 1 月 2 日开始，早于其模拟上市日；000905 从 1 月 5 日开始，
    后续每个交易日上涨 10%。这些数据用于区分行情首日、上市日和用户指定的起始日。
    """
    monkeypatch.setattr(analyser_module, "export_as_api", lambda func: func)
    calendar = pd.bdate_range("2024-01-02", "2024-01-10")
    instruments = {
        "000300.XSHG": mock_instrument(
            "000300.XSHG", _type="INDX", listed_date="2024-02-01", de_listed_date="2999-12-31"
        ),
        "000905.XSHG": mock_instrument(
            "000905.XSHG", _type="INDX", listed_date="2024-01-05", de_listed_date="2999-12-31"
        ),
    }
    bars = {
        "000300.XSHG": np.array([
            (20240102000000, 100), (20240103000000, 101), (20240104000000, 102),
            (20240105000000, 103), (20240108000000, 104), (20240109000000, 105),
            (20240110000000, 106),
        ], dtype=[("datetime", "u8"), ("close", "f8")]),
        "000905.XSHG": np.array([
            (20240105000000, 100), (20240108000000, 110),
            (20240109000000, 121), (20240110000000, 133.1),
        ], dtype=[("datetime", "u8"), ("close", "f8")]),
    }

    def history_bars(instrument, bar_count, frequency, fields, dt, **kwargs):
        assert frequency == "1d"
        data = bars[instrument.order_book_id]
        data = data[data["datetime"] <= convert_date_to_int(dt)]
        if bar_count is not None:
            data = data[-bar_count:]
        return data if fields is None else data[fields]

    def start(benchmark, start_date=date(2024, 1, 2), end_date=date(2024, 1, 10), frequency="1d"):
        registry = HookRegistry()
        env = SimpleNamespace(
            config=RqAttrDict({"base": {
                "start_date": start_date, "end_date": end_date, "frequency": frequency,
            }}),
            hook_registry=registry,
            event_bus=EventBus(registry),
        )
        mod = analyser_module.AnalyserMod()
        mod.start_up(env, RqAttrDict({**__config__, "benchmark": benchmark}))

        # 与 main.run 一致：Mod 先注册，DataProxy 随后才就绪。
        data_source = Mock(spec=AbstractDataSource)
        data_source.get_instruments.side_effect = lambda id_or_syms: [instruments[oid] for oid in id_or_syms]
        data_source.get_trading_calendars.return_value = {TRADING_CALENDAR_TYPE.CN_STOCK: calendar}
        data_source.available_data_range.return_value = (date(2024, 1, 2), date(2024, 1, 10))
        data_source.history_bars.side_effect = history_bars
        env.data_proxy = DataProxy(data_source, Mock())
        return env, mod, data_source

    return start


@pytest.mark.parametrize("start_date, expected_start", [
    pytest.param(date(2024, 1, 2), date(2024, 1, 8), id="before-first-bar"),
    pytest.param(date(2024, 1, 5), date(2024, 1, 8), id="equal-to-first-bar"),
    pytest.param(date(2024, 1, 9), date(2024, 1, 9), id="already-later"),
])
def test_start_date_and_first_day_benchmark_return(start_analyser, start_date, expected_start):
    """起始日早于或等于基准首日时，跨过周末顺延；已经更晚时保持原日期。

    调整后每个回测日（包括首日）都应能用前一交易日价格计算出 10% 的基准收益。
    """
    env, mod, _ = start_analyser("000905.XSHG", start_date=start_date)

    _adjust_start_date(env.config, env.data_proxy, env.hook_registry)

    assert env.config.base.start_date == expected_start
    assert env.config.base.end_date == date(2024, 1, 10)
    env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))
    env.event_bus.publish_event(Event(EVENT.BEFORE_STRATEGY_RUN))
    state = json.loads(mod.get_state())
    np.testing.assert_allclose(
        state["benchmark_daily_returns"],
        np.full(len(env.config.base.trading_calendar), 0.1),
    )


def test_benchmark_at_global_data_start(start_analyser):
    """全部行情和回测都从 2005-01-04 开始时，应顺延到 01-05，避免缺少前一日价格。

    基准收益计算应正常完成，01-05 和 01-06 的收益分别为 10% 和 -10%，结束日保持不变。
    """
    env, mod, data_source = start_analyser(
        "000300.XSHG", start_date=date(2005, 1, 4), end_date=date(2005, 1, 6)
    )
    data_source.available_data_range.return_value = (date(2005, 1, 4), date(2005, 1, 6))
    # 交易日历有前一交易日，但所有行情都从 2005-01-04 开始，无法取得更早的收盘价。
    data_source.get_trading_calendars.return_value = {
        TRADING_CALENDAR_TYPE.CN_STOCK: pd.to_datetime([
            "2004-12-31", "2005-01-04", "2005-01-05", "2005-01-06",
        ]),
    }
    data_source.get_instruments.side_effect = None
    data_source.get_instruments.return_value = [mock_instrument(
        "000300.XSHG", _type="INDX", listed_date="2005-04-08", de_listed_date="2999-12-31"
    )]
    bars = np.array([
        (20050104000000, 100), (20050105000000, 110), (20050106000000, 99),
    ], dtype=[("datetime", "u8"), ("close", "f8")])

    def history_bars(instrument, bar_count, frequency, fields, dt, **kwargs):
        data = bars[bars["datetime"] <= convert_date_to_int(dt)]
        return data[fields]

    data_source.history_bars.side_effect = history_bars

    _adjust_start_date(env.config, env.data_proxy, env.hook_registry)
    env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))
    env.event_bus.publish_event(Event(EVENT.BEFORE_STRATEGY_RUN))

    assert env.config.base.start_date == date(2005, 1, 5)
    assert env.config.base.end_date == date(2005, 1, 6)
    assert list(env.config.base.trading_calendar.date) == [date(2005, 1, 5), date(2005, 1, 6)]
    state = json.loads(mod.get_state())
    np.testing.assert_allclose(state["benchmark_daily_returns"], [0.1, -0.1])


@pytest.mark.parametrize("benchmark", [
    # 字符串配置：两个正权重基准，取第二条日线日期较晚的那个。
    "000300.XSHG:0.5,000905.XSHG:0.5",
    # 反转基准顺序并加入负权重和现金项，日期下限应保持一致。
    "000905.XSHG:-1,000300.XSHG:2,null:1",
    # 字典配置：零权重基准仍按现有取数规则参与日期限制。
    {"000300.XSHG": 1, "000905.XSHG": 0},
])
def test_multiple_benchmarks_use_latest_second_bar(start_analyser, benchmark):
    """复合基准的第二条日线分别为 1 月 3 日和 8 日，回测统一从 1 月 8 日开始。

    验证字符串和字典配置，以及顺序、权重和 null 项不会改变取最晚可用起始日的规则。
    """
    env, _, _ = start_analyser(benchmark)

    _adjust_start_date(env.config, env.data_proxy, env.hook_registry)

    assert env.config.base.start_date == date(2024, 1, 8)


@pytest.mark.parametrize("frequency", ["1d", "1m", "tick"])
def test_uses_daily_quotes_before_index_listed_date(start_analyser, frequency):
    """指数上市前已有日线时，按实际行情首日限制起始日，不能使用上市日期。

    日、分钟和 tick 回测都按基准日线计算下限，本例应从 1 月 3 日开始。
    """
    env, _, _ = start_analyser("000300.XSHG", frequency=frequency)

    _adjust_start_date(env.config, env.data_proxy, env.hook_registry)

    assert env.config.base.start_date == date(2024, 1, 3)


@pytest.mark.parametrize("benchmark", [None, "null", "NULL"])
def test_no_real_benchmark_leaves_range_unchanged(start_analyser, benchmark):
    """未设置基准或仅设置 null/NULL 现金基准时，不调整日期，也不查询基准行情。"""
    env, _, data_source = start_analyser(benchmark)

    _adjust_start_date(env.config, env.data_proxy, env.hook_registry)

    assert env.config.base.start_date == date(2024, 1, 2)
    assert env.config.base.end_date == date(2024, 1, 10)
    data_source.history_bars.assert_not_called()


@pytest.mark.parametrize("second_bar_date", [
    pytest.param(date(2024, 1, 8), id="weekend"),
    pytest.param(date(2024, 1, 9), id="weekend-and-holiday"),
])
def test_hook_uses_second_benchmark_bar(start_analyser, second_bar_date):
    """仅有两条日线也足以计算首日收益，Hook 直接以第二条日线日期作为起始下限。

    覆盖周末及模拟休市日造成的行情间隔，不经过框架的日期对齐。
    """
    env, _, data_source = start_analyser("000905.XSHG")
    data_source.history_bars.side_effect = None
    data_source.history_bars.return_value = np.array([
        convert_date_to_int(date(2024, 1, 5)), convert_date_to_int(second_bar_date),
    ], dtype="u8")
    current = (date(2024, 1, 2), date(2024, 1, 10))

    result = env.hook_registry.hook(AVAILABLE_DATA_RANGE).apply(current, "1d")

    assert result == (second_bar_date, date(2024, 1, 10))
    assert env.config.base.start_date == date(2024, 1, 2)


@pytest.mark.parametrize("current_start, expected_start", [
    pytest.param(date(2024, 1, 9), date(2024, 1, 9), id="trading-day"),
    pytest.param(date(2024, 1, 6), date(2024, 1, 8), id="weekend"),
])
def test_hook_preserves_stricter_incoming_range(start_analyser, current_start, expected_start):
    """起点取传入下限与基准第二条日线日期的较晚者，保留结束日，且不直接修改全局配置。"""
    env, _, _ = start_analyser("000905.XSHG")
    current = (current_start, date(2024, 1, 9))

    assert env.hook_registry.hook(AVAILABLE_DATA_RANGE).apply(current, "1d") == (expected_start, current[1])
    assert env.config.base.start_date == date(2024, 1, 2)


@pytest.mark.parametrize("data", [
    pytest.param(None, id="none"),
    pytest.param(np.array([], dtype="u8"), id="empty"),
    pytest.param(np.array([20240105000000], dtype="u8"), id="single-bar"),
])
def test_benchmark_with_insufficient_data_reports_instrument(start_analyser, data):
    """行情返回 None、空数组或仅一条日线时，抛出包含基准代码的缺数错误。"""
    env, _, data_source = start_analyser("000905.XSHG")
    data_source.history_bars.side_effect = None
    data_source.history_bars.return_value = data

    with pytest.raises(RuntimeError, match=r"000905\.XSHG"):
        _adjust_start_date(env.config, env.data_proxy, env.hook_registry)


def test_no_benchmark_data_before_requested_end(start_analyser):
    """基准从 1 月 5 日才有数据，但用户要求 1 月 4 日结束时，应报缺数错误。"""
    env, _, _ = start_analyser("000905.XSHG", end_date=date(2024, 1, 4))

    with pytest.raises(RuntimeError, match=r"000905\.XSHG"):
        _adjust_start_date(env.config, env.data_proxy, env.hook_registry)


def test_unknown_benchmark_reports_instrument(start_analyser):
    """基准代码不存在时，保留 InstrumentNotFound 异常，并在错误中指出该代码。"""
    env, _, data_source = start_analyser("UNKNOWN.XSHG")
    data_source.get_instruments.side_effect = None
    data_source.get_instruments.return_value = []

    with pytest.raises(InstrumentNotFound, match=r"UNKNOWN\.XSHG"):
        _adjust_start_date(env.config, env.data_proxy, env.hook_registry)


def test_only_one_benchmark_bar_before_requested_end(start_analyser):
    """结束日恰为基准首日时，只能查到一条日线，Hook 应直接报缺数错误。"""
    env, _, _ = start_analyser("000905.XSHG", end_date=date(2024, 1, 5))

    with pytest.raises(RuntimeError, match=r"000905\.XSHG"):
        env.hook_registry.hook(AVAILABLE_DATA_RANGE).apply((date(2024, 1, 2), date(2024, 1, 5)), "1d")
