# -*- coding: utf-8 -*-

import tushare as ts
import pytest

from rqalgoengine.data import RqDataProxy, MyDataProxy


@pytest.fixture()
def trading_calendar():
    trading_cal = ts.trade_cal()["calendarDate"].apply(lambda x: "%s-%02d-%02d" % tuple(map(int, x.split("/"))))
    trading_cal = trading_cal[
        (trading_cal >= "2013-02-01") & (trading_cal <= "2013-05-01")
    ]
    return trading_cal.tolist()


@pytest.fixture()
def rq_data_proxy():
    data_proxy = RqDataProxy()
    return data_proxy
