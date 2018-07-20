from rqalpha.api import *

from ...utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "accounts": {
                "stock": 100000000
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
        },
    }, test_strategies)


@as_test_strategy({
    "base": {
        "start_date": "2015-12-25",
        "end_date": "2016-01-05"
    }
})
def test_stock_account_settlement():
    def init(context):
        # 招商地产
        context.s = "000024.XSHE"
        context.counter = 0

    def handle_bar(context, _):
        context.counter += 1
        if context.counter == 1:
            order_shares(context.s, 10000)
        print(context.portfolio.total_value)

    return init, handle_bar
