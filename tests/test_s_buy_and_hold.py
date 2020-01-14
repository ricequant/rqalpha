def init(context):
    context.s1 = "000001.XSHE"


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    order_shares(context.s1, 1000)


def after_trading(context):
    pass


__config__ = {
    "base": {
        "start_date": "2015-01-09",
        "end_date": "2016-01-12",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": "000300.XSHG",
        "accounts": {
            "stock": 1000000
        }
    },
    "extra": {
        "log_level": "error",
        "show": True,
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}
