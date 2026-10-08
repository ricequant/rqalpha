# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from rqalpha.utils.testing.integration import _assert_dafaframe, _normalize_dtypes


def _frame(unit):
    index = pd.to_datetime(["2020-01-02", "2020-01-03"]).as_unit(unit)
    return pd.DataFrame({"dt": index, "x": [1.0, 2.0]}, index=index)


@pytest.mark.skipif(
    not hasattr(pd.DatetimeIndex, "as_unit"),
    reason="当前 pandas 不支持 DatetimeIndex.as_unit",
)
def test_normalize_datetime_unit():
    result = _frame("us")
    expected = _frame("ns")
    assert result["dt"].dtype != expected["dt"].dtype

    normalized = _normalize_dtypes(result)
    assert normalized["dt"].dtype == "datetime64[ns]"
    assert normalized.index.dtype == "datetime64[ns]"

    _assert_dafaframe(result, expected)

    expected.loc[expected.index[0], "x"] = 3.0
    with pytest.raises(AssertionError):
        _assert_dafaframe(result, expected)
