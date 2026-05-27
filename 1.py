from datetime import date

from rqalpha import run_func
from rqalpha.apis import order_shares, get_position, buy_open, buy_close, sell_open, sell_close


__config__ = {
    "base": {
        "start_date": "2025-10-09",
        "end_date": "2025-12-31",
        "accounts": {
            "stock": 10000000,
            "future": 10000000
        },
        "capital_gain_tax_rate": 0.0318
    }
}


def init(context):
    context.s1 = "000001.XSHE"
    context.f1 = "IM2512"
    context.fired = False


def handle_bar(context, bar_dict):
    if not context.fired:
        order_shares(context.s1, 500)
        sell_open(context.f1, 2)
        context.fired = True

    if context.now.date() == date(2025, 10, 10):
        order_shares(context.s1, 500)
        sell_open(context.f1, 2)

    if context.now.date() == date(2025, 10, 17):
        order_shares(context.s1, -600)
        buy_close(context.f1, 3)
    
    elif context.now.date() == date(2025, 12, 1):
        order_shares(context.s1, -300)

    # elif context.now.date() == date(2025, 3, 31):
    #     print()


if __name__ == "__main__":
    run_func(config=__config__, init=init, handle_bar=handle_bar)