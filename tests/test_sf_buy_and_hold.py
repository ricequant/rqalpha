# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # context内引入全局变量counter
    context.counter = 0
    subscribe('IH88')


# before_trading此函数会在每天交易开始前被调用，当天只会被调用一次
def before_trading(context):
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在总的投资组合信息
    # context.stock_portfolio 可以拿到当前股票子组合的信息
    # context.future_portfolio 可以拿到当前期货子组合的信息
    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    context.counter += 1
    if context.counter == 1:
        # 买入50ETF
        order_shares('510050.XSHG', 330000)
        # 卖出开仓50股指期货一手
        sell_open('IH88', 1)


# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass


__config__ = {
    "base": {
        "start_date": "2016-06-01",
        "end_date": "2016-10-05",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": None,
        "accounts": {
            "stock": 1000000,
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
    },
}
