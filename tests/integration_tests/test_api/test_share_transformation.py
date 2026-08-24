from datetime import date

from rqalpha import run_func
from rqalpha.apis import *


def test_share_transformation():
    """
    测试股票发生代码转换
    """
    config = {
        "base": {
            "start_date": "2025-01-02",
            "end_date": "2025-05-01",
            "accounts": {
                "stock": 1000000
            }
        }
    }

    def init(context):
        context.old = "600837.XSHG"
        context.new = "601211.XSHG"
        context.fired = False

    def handle_bar(context, bar_dict):
        if not context.fired:
            order_target_percent(context.old, 1)
            context.fired = True

        if context.now.date() == date(2025, 3, 3):
            # 还未发生代码转换，此时仍存在旧仓位
            assert get_position(context.old).quantity == 93500
            context.cash = context.portfolio.stock_account.cash

        elif context.now.date() == date(2025, 3, 4):
            # 发生代码转换，具体转换信息为：600837.XSHG -> 601211.XSHG, ratio=0.62
            assert get_position(context.old).quantity == 0
            assert get_position(context.new).quantity == 57970
            assert context.portfolio.stock_account.cash == context.cash

    run_func(config=config, init=init, handle_bar=handle_bar)