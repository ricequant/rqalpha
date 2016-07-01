# -*- coding: utf-8 -*-
from six import print_ as print
import tushare as ts

from rqalgoengine.data import RqDataProxy, MyDataProxy
from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.scope.api import order_shares


def test_Strategy():

    def init(context):
        print("init", context)

    def before_trading(context):
        print("before_trading", context)

    def handle_bar(context, bar_dict):
        print(context.now)
        print("handle_bar", context, bar_dict)
        print(bar_dict["000001.XSHE"])
        print(bar_dict["600485.XSHG"])
        print(bar_dict["600099.XSHG"])
        print(context.portfolio)
        order_shares("000001.XSHG", 100)

    data_proxy = MyDataProxy()
    data_proxy = RqDataProxy()

    trading_calendar = ts.trade_cal()["calendarDate"].apply(lambda x: "%s-%02d-%02d" % tuple(map(int, x.split("/"))))
    trading_calendar = trading_calendar[
        (trading_calendar >= "2013-02-01") & (trading_calendar <= "2013-05-01")
    ]
    trading_calendar = trading_calendar.tolist()

    strategy = Strategy(init, before_trading, handle_bar)
    executor = StrategyExecutor(strategy, data_proxy, trading_calendar)

    perf = executor.execute()
