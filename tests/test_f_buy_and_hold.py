def init(context):
    context.s1 = "IF88"
    subscribe(context.s1)
    logger.info("Interested in: " + str(context.s1))


def handle_bar(context, bar_dict):
    buy_open(context.s1, 1)


__config__ = {
    "base": {
        "start_date": "2015-01-09",
        "end_date": "2015-03-09",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": None,
        "accounts": {
            "future": 1000000
        }
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
