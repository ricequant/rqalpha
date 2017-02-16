def init(context):
    context.s1 = '000905.XSHG'
    subscribe(context.s1)


def handle_bar(context, bar_dict):
    # stocknum = 50
    his = history_bars(context.s1, 10, '1d', 'close')

    # print(his)

    if his[9] / his[8] < 0.97:
        if len(context.portfolio.positions) > 0:
            for stock in context.portfolio.positions.keys():
                order_target_percent(stock, 0)
        return

        # 分配资金
        # if len(context.portfolio.positions) < stocknum:
        # Num = stocknum - len(context.portfolio.positions)
        # Cash = context.portfolio.cash/Num
        # else:
        # Cash = context.portfolio.cash

    # Buy
    # 求出持有该股票的仓位，买入没有持仓并符合条件股票
    position = context.portfolio.positions[context.s1].quantity
    # print(position)
    if position < 100:
        High = history_bars(context.s1, 3, '1d', 'high')
        Low = history_bars(context.s1, 3, '1d', 'low')
        Close = history_bars(context.s1, 3, '1d', 'close')
        Open = history_bars(context.s1, 3, '1d', 'open')

        # logger.info(High)

        HH = max(High[:2])
        LC = min(Close[:2])
        HC = max(Close[:2])
        LL = min(Low[:2])
        Openprice = Open[2]
        # logger.info(HH)
        # print(LC)
        # print(HC)
        # print(LL)
        # print(Openprice)

        # 使用第n-1日的收盘价作为当前价
        current_price = Close[2]


        Range = max((HH - LC), (HC - LL))
        K1 = 0.9
        BuyLine = Openprice + K1 * Range
        # print(BuyLine,'buyline')
        if current_price > BuyLine:
            order_target_percent(context.s1, 1)

    hist = history_bars(context.s1, 3, '1d', 'close')
    case1 = (1 - hist[2] / hist[0]) >= 0.06
    case2 = hist[1] / hist[0] <= 0.92
    if case1 or case2:
        order_target_percent(context.s1, 0)


__config__ = {
    "base": {
        "strategy_type": "stock",
        "start_date": "2013-01-01",
        "end_date": "2015-12-29",
        "frequency": "1d",
        "matching_type": "current_bar",
        "stock_starting_cash": 1000000,
        "benchmark": "000300.XSHG",
        "slippage": 0.00123,
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "progress": {
            "enabled": True,
            "priority": 400,
        },
    },
}
