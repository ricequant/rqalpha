# -*- coding: utf-8 -*-

import datetime
import os

import pandas as pd
import pytest
import pytz

from rqbacktest.data import LocalDataProxy
from rqbacktest.trading_params import TradingParams
from rqbacktest.analyser.simulation_exchange import SimuExchange


@pytest.fixture()
def data_proxy():
    return LocalDataProxy(os.environ.get("RQ_LOCAL_STORE", os.path.expanduser("~/.rqbacktest")))


@pytest.fixture()
def trading_calendar():
    trading_cal = data_proxy().get_trading_dates("2005-01-01", "2020-01-01")

    return trading_cal


@pytest.fixture()
def trading_params():
    trading_cal = trading_calendar()

    trading_cal = trading_cal[
        (trading_cal >= "2013-02-01") & (trading_cal <= "2013-05-01")
    ]

    params = TradingParams(trading_cal)
    return params
