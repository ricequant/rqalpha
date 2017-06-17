from rqalpha.api import *
import os
import sys


def init(context):
    strategy_file_path = context.config.base.strategy_file
    sys.path.append(os.path.realpath(os.path.dirname(strategy_file_path)))

    from get_csv_module import get_csv

    IF1706_df = get_csv()
    context.IF1706_df = IF1706_df


def before_trading(context):
    logger.info(context.IF1706_df)


__config__ = {
    "base": {
        "start_date": "2015-01-09",
        "end_date": "2015-01-10",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": None,
        "accounts": {
            "future": 1000000
        }
    },
    "extra": {
        "log_level": "verbose",
    },
}