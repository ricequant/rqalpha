import time

import talib


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.s1 = "000001.XSHE"

    # 设置这个策略当中会用到的参数，在策略中可以随时调用，这个策略使用长短均线，我们在这里设定长线和短线的区间，在调试寻找最佳区间的时候只需要在这里进行数值改动
    context.SHORTPERIOD = 20
    context.LONGPERIOD = 120
    context.count = 0

    print("init")


def before_trading(context):
    print("before_trading", context.count)
    time.sleep(1)


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    print("handle_bar", context.count)
    context.count += 1

    print(context.count, bar_dict["000001.XSHE"].close)
    print(context.count, bar_dict["000001.XSHG"].close)

    print(current_snapshot("000001.XSHE").last)
    print(current_snapshot("000001.XSHG").last)

    order_shares("000001.XSHE", 100)
    order_shares("000001.XSHE", -100)
    print(context.portfolio)
    print(context.portfolio.positions)


def after_trading(context):
    print("after_trading", context.count)
