from typing import List

import pandas as pd
from typing_extensions import assert_type

from rqalpha.api import api_exc_patch, decorate_api_exc, export_as_api
from rqalpha.apis.api_rqdatac import get_factor, get_industry, get_stock_connect, require_explicit_expect_df
from rqalpha.utils.arg_checker import apply_rules


def original(value: int, *, expect_df: bool = False) -> str:
    return str(value)


@export_as_api
def exported(value: int) -> str:
    return str(value)


@export_as_api
@require_explicit_expect_df
@apply_rules()
def stacked(value: int, *, expect_df: bool = False) -> str:
    return str(value)


def check_signatures() -> None:
    guarded = require_explicit_expect_df(original)
    patched = api_exc_patch(original)
    decorated = decorate_api_exc(original)
    checked = apply_rules()(original)
    renamed = export_as_api(original, name="renamed")

    assert_type(exported(1), str)
    assert_type(stacked(1, expect_df=True), str)
    assert_type(guarded(1, expect_df=True), str)
    assert_type(patched(1, expect_df=True), str)
    assert_type(decorated(1, expect_df=True), str)
    assert_type(checked(1, expect_df=True), str)
    assert_type(renamed(1, expect_df=True), str)
    assert_type(get_industry("银行"), List[str])
    assert_type(get_factor("000001.XSHE", "pe_ratio", count=5, expect_df=False), pd.Series)
    assert_type(get_factor("000001.XSHE", "pe_ratio", count=5, expect_df=True), pd.DataFrame)
    assert_type(get_stock_connect("000001.XSHE", fields="shares_holding", expect_df=False), pd.Series)
    assert_type(get_stock_connect("000001.XSHE", fields="shares_holding", expect_df=True), pd.DataFrame)

    # warn_unused_ignores 会保证这些错误参数确实被类型检查器拒绝。
    exported("invalid")  # type: ignore[arg-type]
    stacked("invalid", expect_df=True)  # type: ignore[arg-type]
    guarded("invalid", expect_df=True)  # type: ignore[arg-type]
    patched("invalid", expect_df=True)  # type: ignore[arg-type]
    decorated("invalid", expect_df=True)  # type: ignore[arg-type]
    checked("invalid", expect_df=True)  # type: ignore[arg-type]
    renamed("invalid", expect_df=True)  # type: ignore[arg-type]
    stacked(1, unexpected=True)  # type: ignore[call-arg]
    get_industry(1)  # type: ignore[arg-type]
    get_factor("000001.XSHE", "pe_ratio", count="5", expect_df=False)  # type: ignore[call-overload]
    get_stock_connect("000001.XSHE", fields=1, expect_df=False)  # type: ignore[call-overload]
