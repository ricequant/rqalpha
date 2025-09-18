from typing import Any


from rqalpha.apis import order_shares, instruments, subscribe_event, EVENT


def test_s_tick_size(run_and_assert_result):
    SLIPPAGE = 10
    price = 0
    stock = "000001.XSHE"

    def init(context):
        context.count = 0
        context.tick_size = instruments(stock).tick_size()
        subscribe_event(EVENT.TRADE, on_trade)

    def on_trade(context, event):
        global price
        trade = event.trade
        assert trade.last_price == price + context.tick_size * SLIPPAGE

    def handle_bar(context, bar_dict):
        global price
        if context.count == 1:
            price = bar_dict[stock].close
            order_shares(stock, 100)
        context.count += 1

    config: dict[str, Any] = {
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

    return run_and_assert_result(config=config, init=init, handle_bar=handle_bar)
