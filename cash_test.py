from rqalpha_plus import run_func
from rqalpha_plus.apis import *

config = {
    "base": {
        "start_date": "2024-03-01",
        "end_date": "2024-03-01",
        "frequency": "tick",
        "accounts": {
            "stock": 11550,
            "future": 84740
        },
    },
    "mod": {
        "sys_simulation": {
            "slippage": 0.1
        },
    }
}


def init(context):
    context.s1 = "000001.XSHE"
    context.s2 = "600000.XSHG"
    context.f1 = "AG2406"
    context.fired = False
    subscribe(context.s1)
    # subscribe(context.f1)


def handle_bar(context, bar_dict):
    if not context.fired:
        order_shares(context.s1, 1000)
        buy_open(context.f1, 10)
        context.fired = True


def handle_tick(context, tick):
    if not context.fired:
        if tick.datetime.minute > 30:
            order_shares(context.s1, 1000)
            # buy_open(context.f1, 10)
            context.fired = True


result = run_func(config=config, init=init, handle_tick=handle_tick)