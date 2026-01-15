from rqalpha import run_func
from rqalpha.apis import *


__config__  = {
    "base": {
        "start_date": "2025-01-01",
        "end_date": "2025-06-01",
        "accounts": {
            "stock": 100000000
        }
    }
}


def init(context):
    context.s1 = "000001.XSHE"
    context.fired = False


def handle_bar(context, bar_dict):
    if not context.fired:
        order_shares(context.s1, 1000)
        context.fired = True


if __name__ == "__main__":
    run_func(config=__config__, init=init, handle_bar=handle_bar)