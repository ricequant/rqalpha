def init(context):
    context.s1 = '600519.XSHG'
    context.fired = False

def before_trading(context):
    pass

def handle_bar(context, bar_dict):
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        order_percent(context.s1, 1)
        context.fired = True


__config__ = {
    "base": {
        "start_date": "2025-01-01",
        "end_date": "2025-06-01",
        "frequency": "1d",
        "matching_type": "current_bar",
        "accounts": {
            "stock": 1000000
        },
        # 严格意义上说A股一年的交易日是242天左右
        "custom_trading_days_a_year": 242
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_analyser": {
            "benchmark": "000300.XSHG",
            "enabled": True,
            "plot": True
        }
    }
}
