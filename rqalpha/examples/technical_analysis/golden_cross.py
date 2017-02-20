# rqalpha run -f rqalpha/examples/technical_analysis/golden_cross.py -sc 100000 -p -bm 000001.XSHE -mc funcat_api.enabled True
from rqalpha.api import *


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.s1 = "000001.XSHE"
    # 当前关注股票为 context.s1
    # S 为 set_current_stock 的简写。等价于 set_current_stock(context.s1)
    S(context.s1)

    # 设置这个策略当中会用到的参数，在策略中可以随时调用，这个策略使用长短均线，我们在这里设定长线和短线的区间，在调试寻找最佳区间的时候只需要在这里进行数值改动
    context.SHORTPERIOD = 20
    context.LONGPERIOD = 120


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    short_ma = MA(C, context.SHORTPERIOD)
    long_ma = MA(C, context.LONGPERIOD)

    plot("short ma", short_ma.value)
    plot("long ma", long_ma.value)

    # 计算现在portfolio中股票的仓位
    cur_position = context.portfolio.positions[context.s1].quantity

    # 如果短均线从上往下跌破长均线，也就是在目前的bar短线平均值低于长线平均值，而上一个bar的短线平均值高于长线平均值
    if cross(long_ma, short_ma) and cur_position > 0:
        # 进行清仓
        order_target_percent(context.s1, 0)

    # 如果短均线从下往上突破长均线，为入场信号
    if cross(short_ma, long_ma):
        # 满仓入股
        order_target_percent(context.s1, 1)
