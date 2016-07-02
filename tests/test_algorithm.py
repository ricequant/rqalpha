# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.data import RqDataProxy, MyDataProxy
from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.scope.api import order_shares

from .fixture import *


def test_Strategy(trading_calendar, rq_data_proxy):

    def init(context):
        print("init", context)
        context.dates = []

    def before_trading(context):
        print("before_trading", context.now)

    def handle_bar(context, bar_dict):
        print(context.now)
        print("handle_bar", context, bar_dict)
        print(bar_dict["000001.XSHE"])
        print(bar_dict["600485.XSHG"])
        print(bar_dict["600099.XSHG"])
        print(context.portfolio)
        order_shares("000001.XSHG", 100)

    strategy = Strategy(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,
    )
    executor = StrategyExecutor(strategy, rq_data_proxy, trading_calendar)

    perf = executor.execute()
