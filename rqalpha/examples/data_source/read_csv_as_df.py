from rqalpha.api import *


def read_csv_as_df(csv_path):
    import pandas as pd
    data = pd.read_csv(csv_path)
    return data


def init(context):
    import os
    strategy_file_path = context.config.base.strategy_file
    csv_path = os.path.join(os.path.dirname(strategy_file_path), "../IF1706_20161108.csv")
    IF1706_df = read_csv_as_df(csv_path)
    context.IF1706_df = IF1706_df


def before_trading(context):
    logger.info(context.IF1706_df)


__config__ = {
    "base": {
        "securities": "future",
        "start_date": "2015-01-09",
        "end_date": "2015-01-10",
        "frequency": "1d",
        "matching_type": "current_bar",
        "future_starting_cash": 1000000,
        "benchmark": None,
    },
    "extra": {
        "log_level": "verbose",
    },
}