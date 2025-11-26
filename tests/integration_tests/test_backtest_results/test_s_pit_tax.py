from rqalpha.apis import order_shares

def test_s_pit_tax(run_and_assert_result):
    def init(context):
        context.s1 = "000001.XSHE"
        context.count = 0

    def before_trading(context):
        context.count += 1

    def handle_bar(context, bar_dict):
        order_shares(context.s1, 1000)
        if context.count > 1:
            order_shares(context.s1, -1000)

    config = {
        "base": {
            "start_date": "2023-08-15",
            "end_date": "2023-09-10",
            "frequency": "1d",
            "accounts": {
                "stock": 1000000
            },
        },
        "extra": {
            "log_level": "error",
            "show": True,
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
            "sys_transaction_cost": {
                "pit_tax": True
            }
        }
    }

    run_and_assert_result(config=config, init=init, before_trading=before_trading, handle_bar=handle_bar)
