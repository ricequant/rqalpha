from rqalpha.apis import order_target_percent


def test_s_scheduler(run_and_assert_result):
    def init(context):
        scheduler.run_weekly(rebalance, 1, time_rule=market_open(0, 0)) # type: ignore


    def rebalance(context, bar_dict):
        stock = "000001.XSHE"
        if context.portfolio.positions[stock].quantity == 0:
            order_target_percent(stock, 1)
        else:
            order_target_percent(stock, 0)


    config = {
        "base": {
            "start_date": "2008-07-01",
            "end_date": "2017-01-01",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": "000001.XSHE",
            "accounts": {
                "stock": 100000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
            "sys_transaction_cost": {
                # 默认印花税修改成万5，2倍才是原来的千1
                "tax_multiplier": 2,
            },

        },
    }
    return run_and_assert_result(config=config, init=init, rebalance=rebalance)
