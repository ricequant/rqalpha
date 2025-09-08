import os
from warnings import warn

import pickle

from pandas import DataFrame

from rqalpha import run_func


def _assert_dafaframe(result: DataFrame, expected_result: DataFrame, exclude_columns: list | None = None):
    if exclude_columns:
        result = result.drop(exclude_columns, axis=1)
        expected_result = expected_result.drop(exclude_columns, axis=1)
    assert result.equals(expected_result)


def _assert_result(result: dict, expected_result: dict):
    actual=  result["sys_analyser"]
    expected = expected_result["sys_analyser"]
    _assert_dafaframe(actual["trades"], expected["trades"], exclude_columns=["order_id", "exec_id"])

    for field in [
        "stock_positions",
        "future_positions",
        "stock_account",
        "future_account",
        "portfolio",
    ]:
        if field in expected:
            _assert_dafaframe(actual[field], expected[field])
    
    for summary_field in expected["summary"]:
        assert actual["summary"][summary_field] == expected["summary"][summary_field]


def integration_test(result_file: str, **kwargs):
    result = run_func(**kwargs)
    if not os.path.exists(result_file):
        warn(f"Result file {result_file} not found, creating it")
        with open(result_file, "wb") as f:
            pickle.dump(result, f)
        return
    with open(result_file, "rb") as f:
        expected_result = pickle.load(f)
    _assert_result(result, expected_result)    



