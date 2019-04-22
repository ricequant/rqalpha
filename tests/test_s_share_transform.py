# rqalpha run -f rqalpha/examples/technical_analysis/golden_cross.py -sc 100000 -p -bm 000001.XSHE -mc funcat_api.enabled True
from rqalpha.api import *


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.predecessor = "601299.XSHG"
    context.successor = "601766.XSHG"


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    order_shares(context.predecessor, 1000)


def after_trading(context):
    if context.now.date() == context.run_info.end_date:
        assert context.portfolio.positions[context.predecessor].quantity == 0
        assert context.portfolio.positions[context.successor].quantity > 0


__config__ = {
    "base": {
        "start_date": "2015-01-01",
        "end_date": "2015-05-31",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": "000300.XSHG",
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
        "sys_funcat": {
            "enabled": True,
            "show": True,
        },
    },
}
