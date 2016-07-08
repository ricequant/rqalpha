# -*- coding: utf-8 -*-

from pprint import pprint

from six import print_ as print, iteritems
import tushare as ts

from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.scope.api import order_shares
from .fixture import *


def test_strategy_print_call(trading_env, data_proxy):

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
        data_proxy=data_proxy,
        trading_env=trading_env,
    )
    executor = StrategyExecutor(
        strategy=strategy,
        trading_env=trading_env,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_load_data(trading_env, data_proxy):

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
        data_proxy=data_proxy,
        trading_env=trading_env,
    )
    executor = StrategyExecutor(
        strategy=strategy,
        trading_env=trading_env,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    assert len(strategy.close) == len(trading_env.trading_calendar)
    assert strategy.close[-1] == data_proxy.get_bar(strategy.stock, trading_env.trading_calendar[-1])["close"]


def test_strategy_portfolio(trading_env, data_proxy):

    def handle_bar(context, bar_dict):
        pass
        # print(context.portfolio)

    strategy = Strategy(
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


def test_strategy_order(trading_env, data_proxy):

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 100)

    strategy = Strategy(
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


def test_strategy_keep_buy(trading_env, data_proxy):

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 1000)
        print(context.now)
        print(context.portfolio.positions["000001.XSHE"])
        print(context.portfolio.cash, context.portfolio.market_value, context.portfolio.portfolio_value)

    strategy = Strategy(
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

    pprint(strategy._simu_exchange.trades)
    for date, portfolio in iteritems(strategy._simu_exchange.daily_portfolios):
        print(date)
        pprint(portfolio)


def test_strategy_buy_and_sell(trading_env, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        context.cnt += 1

        if context.cnt == 2:
            order_shares("000001.XSHE", 5000)
            order_shares("000001.XSHE", -5000)
        if context.cnt == 3:
            order_shares("000001.XSHE", -5000)
        if context.cnt == 4:
            order_shares("000001.XSHE", -5000)

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

    position = strategy._simu_exchange.positions["000001.XSHE"]
    assert position.quantity == 0
    assert position.sellable == 0

    pprint(strategy._simu_exchange.trades)
    for date, portfolio in iteritems(strategy._simu_exchange.daily_portfolios):
        print(date)
        pprint(portfolio)


def test_strategy_sell_no_sellable(trading_env, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 5000)
        order_shares("000001.XSHE", -5000)

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

    pprint(strategy._simu_exchange.trades)
    pprint(strategy._simu_exchange.positions)
