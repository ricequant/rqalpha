# -*- coding: utf-8 -*-
import datetime

from rqalpha.strategy import StrategyExecutor
from rqalpha.api import *
from .fixture import *


def test_schedule(trading_params, data_proxy):
    run_at = []

    def should_not_call(c, d):
        raise RuntimeError('should not call')

    def is_weekday(dt, weekday):
        assert(dt.isoweekday() == weekday)

    def week_of(dt):
        weekday = dt.isoweekday()
        weekend = dt + datetime.timedelta(days=7-weekday)
        start = weekend - datetime.timedelta(days=6)
        return start, weekend

    def is_nth_trading_day_in_week(dt, nth):
        week = data_proxy.get_trading_dates(*week_of(dt))
        if nth > 0:
            nth -= 1
        assert(dt == week[nth].date())

    def month_of(dt):
        start = dt.replace(day=1)
        try:
            end = dt.replace(month=dt.month+1, day=1)
        except ValueError:
            end = dt.replace(year=dt.year+1, month=1, day=1)
        end = end - datetime.timedelta(1)
        return start, end

    def is_nth_trading_day_in_month(dt, nth):
        month = data_proxy.get_trading_dates(*month_of(dt))
        if nth > 0:
            nth -= 1
        assert(dt == month[nth].date())

    def init(context):
        scheduler.run_daily(lambda c, bar_dict: run_at.append(c.now))
        for i in range(1, 8):
            scheduler.run_weekly((lambda n: lambda c, _: is_weekday(c.now.date(), n))(i), weekday=i)

        for i in range(-5, 0):
            scheduler.run_weekly((lambda n: lambda c, _: is_nth_trading_day_in_week(c.now.date(), n))(i), tradingday=i)

        for i in range(1, 6):
            scheduler.run_weekly((lambda n: lambda c, _: is_nth_trading_day_in_week(c.now.date(), n))(i), tradingday=i)

        for i in range(-23, 0):
            scheduler.run_monthly((lambda n: lambda c, _: is_nth_trading_day_in_month(c.now.date(), n))(i),
                                  tradingday=i)

        for i in range(1, 24):
            scheduler.run_monthly((lambda n: lambda c, _: is_nth_trading_day_in_month(c.now.date(), n))(i),
                                  tradingday=i)

    def before_trading(context, bar_dict):
        pass

    def handle_bar(context, bar_dict):
        pass

    executor = StrategyExecutor(
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    scheduler.set_trading_dates(data_proxy.get_trading_dates('2005-01-04', datetime.date.today()))

    perf = executor.execute()
    assert(len(run_at) == len(trading_params.trading_calendar))
