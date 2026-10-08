from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from rqalpha.const import TRADING_CALENDAR_TYPE
from rqalpha.data.trading_dates_mixin import TradingDatesMixin
from rqalpha.mod.rqalpha_mod_sys_analyser.mod import AnalyserMod
from rqalpha.utils.datetime_func import convert_date_to_int


TRADING_DATES = pd.to_datetime(["2005-01-04", "2005-01-05", "2005-01-06"])
BENCHMARKS = ["000300.XSHG", "930930.INDX"]


def make_analyser(
    start_date,
    closes,
    benchmark="000300.XSHG",
    trading_dates=TRADING_DATES,
    bar_dates=None,
    benchmark_calendar=None,
):
    if bar_dates is None:
        bar_dates = trading_dates
    if benchmark_calendar is None:
        benchmark_calendar = trading_dates
    bars = np.array(
        list(zip(convert_date_to_int(bar_dates), closes)),
        dtype=[("datetime", "u8"), ("close", "f8")],
    )
    instrument = SimpleNamespace(
        order_book_id=benchmark,
        listed_date=trading_dates[0].to_pydatetime(),
        de_listed_date=pd.Timestamp("2099-01-01").to_pydatetime(),
    )
    data_source = SimpleNamespace(
        get_trading_calendars=lambda: {
            TRADING_CALENDAR_TYPE.CN_STOCK: trading_dates,
            TRADING_CALENDAR_TYPE.SOUTHBOUND: benchmark_calendar,
        }
    )
    proxy = TradingDatesMixin(data_source)

    def history_bars(**kwargs):
        return bars[bars["datetime"] <= convert_date_to_int(kwargs["dt"])]

    proxy.history_bars = history_bars
    proxy.instrument_not_none = lambda _order_book_id: instrument
    mod = AnalyserMod()
    mod._benchmark = [(benchmark, 1.0)]
    mod._env = SimpleNamespace(
        data_proxy=proxy,
        config=SimpleNamespace(
            base=SimpleNamespace(
                start_date=pd.Timestamp(start_date).date(),
                end_date=trading_dates[-1].date(),
            )
        ),
    )
    return mod


@pytest.mark.parametrize("benchmark", BENCHMARKS)
def test_calendar_start_has_zero_first_return_and_aligned_portfolio(benchmark):
    mod = make_analyser("2005-01-04", [100, 110, 99], benchmark)

    mod.generate_benchmark_daily_returns_and_portfolio(None)

    np.testing.assert_allclose(mod._benchmark_daily_returns, [0.0, 0.1, -0.1])
    assert mod._total_benchmark_portfolios["date"] == list(TRADING_DATES.date)
    np.testing.assert_allclose(mod._total_benchmark_portfolios["unit_net_value"], [1.0, 1.1, 0.99])


@pytest.mark.parametrize("benchmark", BENCHMARKS)
def test_start_after_calendar_beginning_preserves_first_day_return(benchmark):
    mod = make_analyser("2005-01-05", [100, 110, 99], benchmark)

    mod.generate_benchmark_daily_returns_and_portfolio(None)

    np.testing.assert_allclose(mod._benchmark_daily_returns, [0.1, -0.1])
    assert mod._total_benchmark_portfolios["date"] == list(TRADING_DATES[1:].date)
    np.testing.assert_allclose(mod._total_benchmark_portfolios["unit_net_value"], [1.1, 0.99])


@pytest.mark.parametrize("benchmark", BENCHMARKS)
def test_single_day_at_calendar_start_has_zero_return(benchmark):
    mod = make_analyser("2005-01-04", [100], benchmark, trading_dates=TRADING_DATES[:1])

    mod.generate_benchmark_daily_returns_and_portfolio(None)

    np.testing.assert_array_equal(mod._benchmark_daily_returns, [0.0])
    assert mod._total_benchmark_portfolios["date"] == [TRADING_DATES[0].date()]
    np.testing.assert_array_equal(mod._total_benchmark_portfolios["unit_net_value"], [1.0])


@pytest.mark.parametrize("benchmark", BENCHMARKS)
@pytest.mark.parametrize("missing_index", [0, 1])
def test_missing_price_is_not_hidden_by_zero_first_return(benchmark, missing_index):
    mod = make_analyser(
        "2005-01-04",
        np.delete([100, 110, 99], missing_index),
        benchmark,
        bar_dates=TRADING_DATES.delete(missing_index),
    )

    with pytest.raises(RuntimeError):
        mod.generate_benchmark_daily_returns_and_portfolio(None)


def test_missing_date_and_duplicate_date_are_rejected_even_when_counts_match():
    mod = make_analyser(
        "2005-01-04",
        [100, 110, 110],
        bar_dates=TRADING_DATES.take([0, 1, 1]),
    )

    with pytest.raises(RuntimeError):
        mod.generate_benchmark_daily_returns_and_portfolio(None)


def test_non_cn_calendar_holiday_keeps_dates_aligned():
    mod = make_analyser(
        "2005-01-04",
        [100, 99],
        "930930.INDX",
        bar_dates=TRADING_DATES.take([0, 2]),
        benchmark_calendar=TRADING_DATES.take([0, 2]),
    )

    mod.generate_benchmark_daily_returns_and_portfolio(None)

    np.testing.assert_allclose(mod._benchmark_daily_returns, [0.0, 0.0, -0.01])
    assert mod._total_benchmark_portfolios["date"] == list(TRADING_DATES.date)
    np.testing.assert_allclose(mod._total_benchmark_portfolios["unit_net_value"], [1.0, 1.0, 0.99])
