from rqalpha.api import *


def init(context):
    IF1706_df = get_csv_as_df()
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
    "mod": {
        "extend_api_demo": {
            "enabled": True,
            "lib": "rqalpha.examples.extend_api.rqalpha_mod_extend_api_demo",
            "csv_path": "../IF1706_20161108.csv"
        }
    }
}


