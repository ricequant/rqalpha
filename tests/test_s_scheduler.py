from rqalpha.api import *


def init(context):
    scheduler.run_weekly(rebalance, 1, time_rule=market_open(0, 0))


def rebalance(context, bar_dict):
    stock = "000001.XSHE"
    if context.portfolio.positions[stock].quantity == 0:
        order_target_percent(stock, 1)
    else:
        order_target_percent(stock, 0)


__config__ = {
    "base": {
        "securities": "stock",
        "start_date": "2008-07-01",
        "end_date": "2017-01-01",
        "frequency": "1d",
        "matching_type": "current_bar",
        "stock_starting_cash": 100000,
        "benchmark": "000001.XSHE",
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}
