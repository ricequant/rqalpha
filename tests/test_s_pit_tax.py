def init(context):
    context.s1 = "000001.XSHE"
    context.count = 0


def before_trading(context):
    context.count += 1


def handle_bar(context, bar_dict):
    order_shares(context.s1, 1000)
    if context.count > 1:
        order_shares(context.s1, -1000)


def after_trading(context):
    pass


__config__ = {
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