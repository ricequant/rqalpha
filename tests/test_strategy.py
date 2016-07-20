# -*- coding: utf-8 -*-

from pprint import pprint

import numpy as np
from six import iteritems

from rqalpha import StrategyExecutor
from rqalpha.api import order_shares
from rqalpha.trading_params import TradingParams
from .fixture import *


def test_buy_and_sell(trading_calendar, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        context.cnt += 1

        if context.cnt % 2 == 1:
            order_shares("000001.XSHE", 5000)
        else:
            order_shares("000001.XSHE", -5000)


    trading_cal = trading_calendar
    trading_cal = trading_cal[
        (trading_cal >= "2013-02-01") & (trading_cal <= "2013-05-01")
    ]
    trading_params = TradingParams(trading_cal)

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    portfolio = executor.exchange.account.portfolio
    assert np.isclose(portfolio.annualized_returns, -0.094760148802936484)
    assert np.isclose(portfolio.total_returns, -0.022917433828999911)


def test_dividend(trading_calendar, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        context.cnt += 1

        if context.cnt < 3:
            order_shares("000001.XSHE", 5000)

    trading_cal = trading_calendar
    trading_cal = trading_cal[
        (trading_cal >= "2013-02-01") & (trading_cal <= "2013-07-01")
    ]
    trading_params = TradingParams(trading_cal)

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    portfolio = executor.exchange.account.portfolio

    assert np.isclose(portfolio.annualized_returns, -0.47051001393709346)
    assert np.isclose(portfolio.total_returns, -0.23129389564400005)
