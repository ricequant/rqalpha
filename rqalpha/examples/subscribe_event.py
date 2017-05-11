from rqalpha.api import *
from rqalpha import subscribe_event


def on_trade_handler(event):
    trade = event.trade
    order = event.order
    account = event.account
    logger.info("*" * 10 + "Trade Handler" + "*" * 10)
    logger.info(trade)
    logger.info(order)
    logger.info(account)


def on_order_handler(event):
    order = event.order
    logger.info("*" * 10 + "Order Handler" + "*" * 10)
    logger.info(order)


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    logger.info("init")
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    # 是否已发送了order
    context.fired = False
    subscribe_event(EVENT.TRADE, on_trade_handler)
    subscribe_event(EVENT.ORDER_CREATION_PASS, on_order_handler)


def before_trading(context):
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合状态信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        order_percent(context.s1, 1)
        context.fired = True

# rqalpha run -f ./rqalpha/examples/subscribe_event.py -s 2016-06-01 -e 2016-12-01 --stock-starting-cash 100000 --benchmark 000300.XSHG