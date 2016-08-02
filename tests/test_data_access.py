# -*- coding: utf-8 -*-

from pprint import pprint

import pandas as pd
import numpy as np
from six import iteritems

from rqalpha import StrategyExecutor
from rqalpha.api import order_shares
from rqalpha.trading_params import TradingParams
from .fixture import *


def test_get_trading_dates(data_proxy):
    start_date, end_date = pd.Timestamp("2014-01-04"), pd.Timestamp("2014-01-07")
    trading_cal = data_proxy.get_trading_dates(start_date, end_date)

    assert len(trading_cal) == 2


def test_api_last(data_proxy):
    data = data_proxy.last("000002.XSHE", pd.Timestamp("2016-07-06"), 60, "1d", "date")

    assert data[-4] == 20151218000000


def test_api_history(data_proxy):
    data = data_proxy.history("000002.XSHE", pd.Timestamp("2016-07-06"), 60, "1d", "date")

    assert data[-4] == 20160701000000
