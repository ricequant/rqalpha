from rqalpha.environment import Environment

SLIPPAGE = 10
price = 0
futures_1 = "AG1702"  # future_info.json 中存有该合约的数据
futures_2 = "AG1612"  # future_info.json 中不存在该合约的数据，需要通过 underlying_symbol 获取


def init(context):
    context.count = 0

    subscribe_event(EVENT.TRADE, on_trade)


def on_trade(context, event):
    
    global price
    trade = event.trade
    order_book_id = trade.order_book_id
    tick_size = Environment.get_instance().get_instrument(order_book_id).tick_size()
    assert tick_size == 1.0
    assert trade.last_price == price + tick_size * SLIPPAGE


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    global price
    context.count += 1
    if context.count == 1:
        price = bar_dict[futures_1].close
        buy_open(futures_1, 10)
    elif context.count == 2:
        price = bar_dict[futures_2].close
        buy_open(futures_2, 10)


def after_trading(context):
    pass

__config__ = {
    "base": {
        "start_date": "2016-09-01",
        "end_date": "2016-09-30",
        "frequency": "1d",
        "matching_type": "current_bar",
        "accounts": {
            "future": 1000000
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