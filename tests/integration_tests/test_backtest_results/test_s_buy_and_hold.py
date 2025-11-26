from rqalpha.apis import order_shares


def test_s_buy_and_hold(run_and_assert_result):
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        order_shares(context.s1, 1000)

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
        "extra": {
            "log_level": "error",
        },
    }

    run_and_assert_result(config=config, init=init, handle_bar=handle_bar)
