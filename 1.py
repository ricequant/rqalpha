from datetime import date

from rqalpha import run_func
from rqalpha.apis import order_shares, get_position


__config__ = {
    "base": {
        "start_date": "2025-03-04",
        "end_date": "2025-12-31",
        "accounts": {
            "stock": 10000000
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

    if context.now.date() == date(2025, 3, 6):
        order_shares(context.s1, -500)
        get_position(context.s1)
    
    elif context.now.date() == date(2025, 3, 14):
        print(bar_dict[context.s1].last)
        order_shares(context.s1, -300)

    elif context.now.date() == date(2025, 3, 31):
        print()


if __name__ == "__main__":
    run_func(config=__config__, init=init, handle_bar=handle_bar)