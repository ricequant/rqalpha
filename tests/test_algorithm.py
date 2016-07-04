# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.data import RqDataProxy, MyDataProxy
from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.scope.api import order_shares

from .fixture import *


def test_strategy_print_call(trading_env):

    def init(context):
        print("init", context)

    def before_trading(context):
        print("before_trading", context.now)

    def handle_bar(context, bar_dict):
        print(bar_dict["000001.XSHE"])
        print(bar_dict["600485.XSHG"])
        print(bar_dict["600099.XSHG"])
        print(context.now)

    strategy = Strategy(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,
    )
    executor = StrategyExecutor(
        strategy,
        trading_env=trading_env,
    )

    perf = executor.execute()


def test_strategy_load_data(trading_env, rq_data_proxy):

    def init(context):
        print("init", context)
        context.stock = "600099.XSHG"
        context.close = []

    def before_trading(context):
        pass

    def handle_bar(context, bar_dict):
        context.close.append(bar_dict[context.stock].close)

    strategy = Strategy(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,
    )
    executor = StrategyExecutor(
        strategy,
        trading_env=trading_env,
    )

    perf = executor.execute()

    assert len(strategy.close) == len(trading_env.trading_calendar)
    assert strategy.close[-1] == rq_data_proxy.get_data(strategy.stock, trading_env.trading_calendar[-1])["close"]


def test_strategy_portfolio(trading_env):

    def handle_bar(context, bar_dict):
        pass
        # print(context.portfolio)

    strategy = Strategy(
        handle_bar=handle_bar,
    )
    executor = StrategyExecutor(
        strategy,
        trading_env=trading_env,
    )

    perf = executor.execute()
