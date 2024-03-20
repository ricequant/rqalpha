def init(context):
    context.f1 = "IH2402"
    context.f2 = "IC2402"
    context.fired = False


def handle_bar(context, bar_dict):
    if not context.fired:
        buy_open(context.f1, 3)
        sell_open(context.f2, 3)
        context.fired = True


__config__ = {
    "base": {
        "start_date": "2024-02-05",
        "end_date": "2024-02-20",
        "frequency": "1d",
        "accounts": {
            "future": 10000000,
        },
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled":True,
            "show": True,
        },
    },
}