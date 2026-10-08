# -*- coding: utf-8 -*-
import pytest

from rqalpha.apis import api_rqdatac
from rqalpha.const import EXC_TYPE
from rqalpha.utils.exception import RQTypeError, get_exc_from_type

# 各 API 到 count 的位置参数；不含 get_price——其外层 enforce_phase 需要 Environment
COUNT_ARGS = {
    "get_shares": ("000001.XSHE", 3),
    "get_securities_margin": ("000001.XSHE", 3),
    "get_turnover_rate": ("000001.XSHE", 3),
    "get_price_change_rate": ("000001.XSHE", 3),
    "get_factor": ("000001.XSHE", "pe_ratio", 3),
    "get_stock_connect": ("000001.XSHE", 3),
}


def test_binding_error_keeps_user_exception():
    cases = [
        (name, ("000001.XSHE",), {"unknown_argument": 1}, "unexpected keyword argument 'unknown_argument'")
        for name in COUNT_ARGS
    ] + [
        (name, args, {"count": 1}, "multiple values for argument 'count'")
        for name, args in COUNT_ARGS.items()
    ]

    for name, args, kwargs, expected_msg in cases:
        with pytest.raises(RQTypeError) as exc_info:
            getattr(api_rqdatac, name)(*args, **kwargs)
        assert get_exc_from_type(exc_info.value) == EXC_TYPE.USER_EXC, name
        assert expected_msg in str(exc_info.value), name

    # 与未加装饰器、同样走 apply_rules 的 API 逐字对照
    with pytest.raises(RQTypeError) as control_info:
        api_rqdatac.get_split("000001.XSHE", unknown_argument=1)
    with pytest.raises(RQTypeError) as decorated_info:
        api_rqdatac.get_shares("000001.XSHE", unknown_argument=1)
    assert str(decorated_info.value) == str(control_info.value).replace("get_split()", "get_shares()")
