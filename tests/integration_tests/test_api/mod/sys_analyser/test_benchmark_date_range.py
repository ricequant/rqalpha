"""通过公开回测入口和真实 bundle 指数行情验证 benchmark 对回测起止日期的限制。"""

import numpy as np
import pytest

from rqalpha import run_func
from rqalpha.utils.exception import CustomException


@pytest.fixture
def run_backtest():
    def run(benchmark, start_date, end_date):
        return run_func(
            config={
                "base": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "frequency": "1d",
                    "accounts": {"stock": 1000000},
                },
                "extra": {"log_level": "error"},
                "mod": {"sys_analyser": {"benchmark": benchmark}},
            },
            init=lambda context: None,
        )["sys_analyser"]

    return run


def test_benchmark_at_bundle_start(run_backtest):
    """bundle 和沪深 300 行情均从 2005-01-04 开始，回测应顺延一天并正确计算首日收益。"""
    result = run_backtest("000300.XSHG", "2005-01-04", "2005-01-07")

    assert result["summary"]["start_date"] == "2005-01-05"
    assert result["summary"]["end_date"] == "2005-01-07"
    benchmark = result["benchmark_portfolio"]
    assert list(benchmark.index.strftime("%Y-%m-%d")) == ["2005-01-05", "2005-01-06", "2005-01-07"]
    # 沪深 300 的 01-04 收盘价为 982.79，后续净值均以该价格为基准。
    np.testing.assert_allclose(benchmark.unit_net_value, np.array([992.56, 983.17, 983.96]) / 982.79)


@pytest.mark.parametrize("start_date, end_date, expected_start, expected_end", [
    # 000188 的行情从 2017-09-12 开始，到 2017-12-25 结束，收缩复合基准的可回测区间。
    pytest.param("2017-09-11", "2017-12-29", "2017-09-13", "2017-12-25", id="restrict-to-common-range"),
    # 用户指定的区间已落在双方数据范围内，应保留原起止日期。
    pytest.param("2017-09-15", "2017-09-22", "2017-09-15", "2017-09-22", id="preserve-narrower-range"),
])
def test_composite_benchmark_date_range(run_backtest, start_date, end_date, expected_start, expected_end):
    """复合基准取最晚可用起始日和最早结束日；用户指定更窄区间时不扩张。"""
    result = run_backtest("000300.XSHG:0.5,000188.XSHG:0.5", start_date, end_date)

    assert result["summary"]["start_date"] == expected_start
    assert result["summary"]["end_date"] == expected_end
    benchmark = result["benchmark_portfolio"]
    assert benchmark.index.equals(result["portfolio"].index)
    assert benchmark.unit_net_value.notna().all()
