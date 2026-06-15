from rqalpha import run_func
from rqalpha.apis import order_shares


config = {
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
    "mod": {
        "sys_simulation": {
            "partial_fill_on_insufficient_cash": True
        }
    }
}


def init(context):
    pass


def handle_bar(context, bar_dict):
    pass


if __name__ == "__main__":
    run_func(config=config, init=init, handle_bar=handle_bar)