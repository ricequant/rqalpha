def init(context):
    context.s1 = "IF88"
    subscribe(context.s1)
    logger.info("Interested in: " + str(context.s1))


def handle_bar(context, bar_dict):
    buy_open(context.s1, 1)


__config__ = {
    "base": {
        "strategy_type": "future",
        "start_date": "2015-01-09",
        "end_date": "2015-03-09",
        "frequency": "1d",
        "matching_type": "next_bar",
        "future_starting_cash": 1000000,
        "commission_multiplier": 0.01,
        "benchmark": None,
    },
    "extra": {
        "log_level": "error",
        # "plot": True,
    },
    "mod": {
        "progress": {
            "enabled": True,
            "priority": 400,
        },
    },
}
