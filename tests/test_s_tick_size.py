from rqalpha import subscribe_event, events

SLIPPAGE = 10
price = 0
stock = "000001.XSHE"


def init(context):
    context.count = 0
    subscribe_event(events.EVENT.TRADE, on_trade)


def on_trade(event):
    global price
    trade = event.trade
    assert trade.last_price == price + instruments(stock).tick_size() * SLIPPAGE


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    global price
    if context.count == 1:
        price = bar_dict[stock].close
        order_shares(stock, 100)
    context.count += 1


def after_trading(context):
    pass


__config__ = {
    "base": {
        "start_date": "2016-07-01",
        "end_date": "2017-08-01",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": "000300.XSHG",
        "accounts": {
            "stock": 1000000
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
        "sys_simulation": {
            "signal": True,
            "slippage_model": "TickSizeSlippage",
            "slippage": SLIPPAGE,
        }
    },
}
