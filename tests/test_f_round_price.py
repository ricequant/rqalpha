def init(context):
    context.f1 = "I1801"
    context.counter = 0


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    context.counter += 1
    if context.counter == 1:
        order = buy_open(context.f1, 1, 510.75)
        print(order)
        assert order.price == 510.5


def after_trading(context):
    pass


__config__ = {
    "base": {
        "start_date": "2017-02-01",
        "end_date": "2017-03-01",
        "frequency": "1d",
        "matching_type": "current_bar",
        "accounts": {
            "future": 1000000
        },
        "round_price": True,
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
        "sys_simulation": {
            "signal": True,
        }
    },
}
