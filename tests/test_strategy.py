# -*- coding: utf-8 -*-

from pprint import pprint

import numpy as np
from six import print_ as print, iteritems
import tushare as ts

from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.scope.api import order_shares
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
    trading_env = TradingEnv(trading_cal)

    strategy = Strategy(
        init=init,
        handle_bar=handle_bar,
        data_proxy=data_proxy,
        trading_env=trading_env,
    )
    executor = StrategyExecutor(
        strategy=strategy,
        trading_env=trading_env,
        data_proxy=data_proxy,
    )

    perf = executor.execute()
    portfolio = strategy._simu_exchange.portfolio

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
    trading_env = TradingEnv(trading_cal)

    strategy = Strategy(
        init=init,
        handle_bar=handle_bar,
        data_proxy=data_proxy,
        trading_env=trading_env,
    )
    executor = StrategyExecutor(
        strategy=strategy,
        trading_env=trading_env,
        data_proxy=data_proxy,
    )

    perf = executor.execute()
    portfolio = strategy._simu_exchange.portfolio

    assert np.isclose(portfolio.annualized_returns, -0.47051001393709346)
    assert np.isclose(portfolio.total_returns, -0.23129389564400005)
