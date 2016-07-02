# -*- coding: utf-8 -*-

import datetime

import tushare as ts
import pytest
import pytz

from rqalgoengine.data import RqDataProxy, MyDataProxy
from rqalgoengine.trading_env import TradingEnv


@pytest.fixture()
def trading_calendar():
    timezone = pytz.timezone("Asia/Shanghai")

    trading_cal = ts.trade_cal()["calendarDate"].apply(lambda x: "%s-%02d-%02d" % tuple(map(int, x.split("/"))))
    trading_cal = trading_cal[
        (trading_cal >= "2013-02-01") & (trading_cal <= "2013-05-01")
    ]

    trading_cal = [
        datetime.datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone) for date in trading_cal.tolist()
    ]

    return trading_cal


@pytest.fixture()
def trading_env():
    env = TradingEnv(trading_calendar())
    return env


@pytest.fixture()
def rq_data_proxy():
    data_proxy = RqDataProxy()
    return data_proxy
