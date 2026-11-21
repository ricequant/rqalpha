from rqalpha.apis import *

import talib


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递
def init(context):
    # context内引入全局变量s1，存储目标合约信息
    context.s1 = 'IF1606'

    # 使用MACD需要设置长短均线和macd平均线的参数
    context.SHORTPERIOD = 12
    context.LONGPERIOD = 26
    context.SMOOTHPERIOD = 9
    context.OBSERVATION = 50

    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新
    subscribe(context.s1)


# 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑
    # 获取历史收盘价序列，history_bars函数直接返回ndarray，方便之后的有关指标计算
    prices = history_bars(context.s1, context.OBSERVATION, '1d', 'close')

    # 用Talib计算MACD取值，得到三个时间序列数组，分别为macd,signal 和 hist
    macd, signal, hist = talib.MACD(prices, context.SHORTPERIOD,
                                    context.LONGPERIOD, context.SMOOTHPERIOD)

    # macd 是长短均线的差值，signal是macd的均线，如果短均线从下往上突破长均线，为入场信号，进行买入开仓操作
    if macd[-1] - signal[-1] > 0 and macd[-2] - signal[-2] < 0:
        sell_qty = get_position(context.s1, POSITION_DIRECTION.SHORT).quantity
        # 先判断当前卖方仓位，如果有，则进行平仓操作
        if sell_qty > 0:
            buy_close(context.s1, 1)
        # 买入开仓
        buy_open(context.s1, 1)

    if macd[-1] - signal[-1] < 0 and macd[-2] - signal[-2] > 0:
        buy_qty = get_position(context.s1, POSITION_DIRECTION.LONG).quantity
        # 先判断当前买方仓位，如果有，则进行平仓操作
        if buy_qty > 0:
            sell_close(context.s1, 1)
        # 卖出开仓
        sell_open(context.s1, 1)
