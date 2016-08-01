# -*- coding: utf-8 -*-

from pprint import pprint

import numpy as np
from six import iteritems

from rqalpha import StrategyExecutor
from rqalpha.api import *
from .fixture import *


def test_strategy_print_call(trading_params, data_proxy):

    def init(context):
        print("init", context)

    def before_trading(context, bar_dict):
        print("before_trading", context.now)

    def handle_bar(context, bar_dict):
        print(bar_dict["000001.XSHE"])
        print(bar_dict["600485.XSHG"])
        print(bar_dict["600099.XSHG"])
        print(context.now)

    executor = StrategyExecutor(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_load_data(trading_params, data_proxy):

    def init(context):
        print("init", context)
        context.stock = "600099.XSHG"
        context.close = []
        context.dates = []

    def before_trading(context, bar_dict):
        pass

    def handle_bar(context, bar_dict):
        context.dates.append(context.now)
        context.close.append(bar_dict[context.stock].close)

    executor = StrategyExecutor(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    assert len(executor.strategy_context.close) == len(trading_params.trading_calendar)
    assert np.isclose(executor.strategy_context.close[-1],
                      data_proxy.get_bar(executor.strategy_context.stock,
                                         trading_params.trading_calendar[-1]).close)


def test_strategy_portfolio(trading_params, data_proxy):

    def handle_bar(context, bar_dict):
        pass
        # print(context.portfolio)

    executor = StrategyExecutor(
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_order(trading_params, data_proxy):

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 100)

    executor = StrategyExecutor(
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_keep_buy(trading_params, data_proxy):

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 1000)
        print(context.now)
        print(context.portfolio.positions["000001.XSHE"])
        print(context.portfolio.cash, context.portfolio.market_value, context.portfolio.portfolio_value)

    executor = StrategyExecutor(
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_buy_and_sell(trading_params, data_proxy):
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

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    positions = executor.exchange.account.portfolio.positions
    position = positions["000001.XSHE"]
    assert position.quantity == 0
    assert position.sellable == 0


def test_strategy_buy_and_sell2(trading_params, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        context.cnt += 1

        if context.cnt % 2 == 1:
            order_shares("000001.XSHE", 5000)
        else:
            order_shares("000001.XSHE", -5000)

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()

    positions = executor.exchange.account.portfolio.positions
    position = positions["000001.XSHE"]
    assert position.quantity == 0
    assert position.sellable == 0

    pprint(executor.exchange.account.get_all_trades())
    for date, portfolio in iteritems(executor.exchange.daily_portfolios):
        print(date)
        pprint(portfolio)


def test_strategy_sell_no_sellable(trading_params, data_proxy):
    def init(context):
        context.cnt = 0

    def handle_bar(context, bar_dict):
        order_shares("000001.XSHE", 5000)
        order_shares("000001.XSHE", -5000)

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()


def test_strategy_history(trading_params, data_proxy):
    def init(context):
        context.cnt = 0
        update_universe(["000001.XSHE"])

    def handle_bar(context, bar_dict):
        print(history(5, "1d", "close")["000001.XSHE"])

    executor = StrategyExecutor(
        init=init,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    perf = executor.execute()
