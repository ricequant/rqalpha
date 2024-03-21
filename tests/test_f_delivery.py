import datetime

def init(context):
    context.f1 = "IH2402"
    context.f2 = "IC2402"
    context.fired = False


def handle_bar(context, bar_dict):
    if not context.fired:
        buy_open(context.f1, 3)
        sell_open(context.f2, 3)
        context.fired = True
    if bar_dict._dt.date() == datetime.date(2024, 2, 19):
        context.cash_before_delivery = context.portfolio.cash
        context.daily_pnl = context.portfolio.daily_pnl
    if bar_dict._dt.date() == datetime.date(2024, 2, 20):
        assert get_position(context.f1).quantity == 0
        assert get_position(context.f2).quantity == 0
        assert abs(context.portfolio.cash - (((2363 * 300) + (5105.6 * 200)) * 0.12 * 3 + context.cash_before_delivery + context.daily_pnl)) < 0.0000001
        assert context.portfolio.total_value == context.portfolio.cash


__config__ = {
    "base": {
        "start_date": "2024-02-05",
        "end_date": "2024-02-20",
        "frequency": "1d",
        "accounts": {
            "future": 10000000,
        },
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled":True,
            "show": True,
        },
    },
}