from rqalpha.api import *

from ...utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "accounts": {
                "stock": 1000000,
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            }
        },
    }, test_strategies)


@as_test_strategy({
    "base": {
        "start_date": "2015-12-07",
        "end_date": "2016-01-05"
    }
})
def test_stock_account_settlement():
    import datetime

    def init(context):
        # 招商地产
        context.s = "000024.XSHE"
        context.fired = False
        context.total_value_before_delisted = None

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 20000)
            context.fired = True
        if context.now.date() == datetime.date(2015, 12, 29):
            context.total_value_before_delisted = context.portfolio.total_value
        if context.now.date() > datetime.date(2015, 12, 29):
            assert context.portfolio.total_value == context.total_value_before_delisted

    return init, handle_bar
