from rqalpha_plus import run_func
from rqalpha_plus.apis import order_shares, VWAPOrder


def handle_bar(context, bar_dict):
    order = order_shares("002107.XSHE", 100, price_or_style=VWAPOrder(931, 940))
    print(order)
    print(bar_dict["002107.XSHE"])


config = {
    "base": {
        "start_date": "2022-01-04",
        "end_date": "2022-01-04",
        "accounts": {
            "stock": 100000000
        }
    }
}


if __name__ == "__main__":
    run_func(handle_bar=handle_bar, config=config)