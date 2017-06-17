# rqalpha run -f rqalpha/examples/technical_analysis/ama.py -sc 100000 -p -bm 000300.XSHG -mc funcat_api.enabled True
from rqalpha.api import *


def init(context):
    context.s1 = "600275.XSHG"
    S(context.s1)


def handle_bar(context, bar_dict):
    # 自己实现 AMA 指标
    M1 = 5
    M2 = 89
    M3 = 36

    DDD = MA(CLOSE, M1) - MA(CLOSE, M2)
    AMA = MA(DDD, M3)

    plot("DDD", DDD.value)
    plot("AMA", AMA.value)

    cur_position = context.portfolio.positions[context.s1].quantity

    if DDD < AMA and cur_position > 0:
        order_target_percent(context.s1, 0)

    if (HHV(MAX(O, C), 50) / LLV(MIN(O, C), 50) < 2 and CROSS(DDD, AMA) and cur_position == 0):
        order_target_percent(context.s1, 1)


__config__ = {
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
        "sys_funcat": {
            "enabled": True,
            "show": True,
        },
    },
}
