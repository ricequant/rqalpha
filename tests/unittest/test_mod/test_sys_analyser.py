from types import SimpleNamespace

import numpy as np
import pandas as pd

from rqalpha.mod.rqalpha_mod_sys_analyser.mod import AnalyserMod
from rqalpha.utils.datetime_func import convert_date_to_int


def make_trading_dates() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        ["2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06"]
    )


def make_instrument() -> SimpleNamespace:
    return SimpleNamespace(order_book_id="000300.XSHG")


def make_analyser(bars) -> AnalyserMod:
    class FakeDataProxy:
        def history_bars(self, **kwargs):
            return bars

    analyser = AnalyserMod()
    analyser._env = SimpleNamespace(data_proxy=FakeDataProxy())
    return analyser


def make_bars(trading_dates: pd.DatetimeIndex, closes: list[float]) -> pd.DataFrame:
    datetimes = np.array(
        [np.uint64(convert_date_to_int(day.date())) for day in trading_dates],
        dtype=np.uint64,
    )
    return pd.DataFrame({"datetime": datetimes, "close": closes})


def expected_returns(closes: list[float]) -> np.ndarray:
    close_series = pd.Series(closes)
    return (close_series / close_series.shift(1) - 1.0).dropna().to_numpy()


def test_benchmark_returns_with_dataframe_source() -> None:
    trading_dates = make_trading_dates()
    closes = [100.0, 101.0, 99.0, 102.0]
    analyser = make_analyser(make_bars(trading_dates, closes))

    returns = analyser._get_one_benchmark_daily_returns(
        make_instrument(), trading_dates
    )

    np.testing.assert_allclose(returns, expected_returns(closes))


def test_benchmark_returns_with_numpy_records_source() -> None:
    trading_dates = make_trading_dates()
    closes = [100.0, 101.0, 99.0, 102.0]
    bars = make_bars(trading_dates, closes).to_records(index=False)
    analyser = make_analyser(bars)

    returns = analyser._get_one_benchmark_daily_returns(
        make_instrument(), trading_dates
    )

    np.testing.assert_allclose(returns, expected_returns(closes))
