from rqalpha.utils.testing import integration_test
from rqalpha.apis import subscribe, order_shares, sell_open


def test_sf_buy_and_hold(result_file):
    def init(context):
        context.counter = 0
        subscribe('IH88')

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            # 买入50ETF
            order_shares('510050.XSHG', 330000)
            # 卖出开仓50股指期货一手
            sell_open('IH88', 1)

    config = {
        "base": {
            "start_date": "2016-06-01",
            "end_date": "2016-10-05",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "stock": 1000000,
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "error",
        }
    }

    integration_test(result_file, config=config, init=init, handle_bar=handle_bar)
