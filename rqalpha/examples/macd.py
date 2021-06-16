import pandas as pd

from rqalpha import run_func
from rqalpha.apis import *

import talib


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    context.s1 = "000001.XSHE"
    # 开启动态复权模式(真实价格)
    #set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    user_log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    #user_log.set_level('order', 'error')

    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    # set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5),
    #                type='stock')

    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘前运行

    scheduler.run_daily(handle_bar, time_rule=14*60+50)

    # 从这里开始我的
    # 持有股票数量
    g.STOCKCOUNT = 5

def before_trading(context):
    # 当前持有的股票
    g.bought_stocks_o = list(context.portfolio.positions.keys())
    g.bought_stocks = g.bought_stocks_o.copy()  # 记录昨日就持有的股票

    # 当前持仓数量
    g.bought_num = len(context.portfolio.positions)

    # 获取今天日期-90天，过滤掉次新股
    # g.today = datetime.datetime.now()
    # g.today90 = g.today -  timedelta(days=90)

    #g.all_securities = all_instruments(['stock'], g.today90)
    g.all_securities = all_instruments(type='CS')['order_book_id'].tolist()

    # for stocknum in g.all_securities

    # 获得所有股票代码
    # 新上市的股票需要过滤掉，根据上市时间过滤
    g.stocks = g.all_securities

    # 剔除科创板股票
    for tempstock in g.stocks:
        if tempstock.find('68') == 0:  # 开头匹配到68
            g.stocks.remove(tempstock)
            continue
        elif g.bought_stocks.count(tempstock) > 0:  # 已经买了
            g.stocks.remove(tempstock)
            continue
        else:
            continue

    # 得到所有股票昨日收盘价, 每天只需要取一次, 所以放在 before_trading_start 中
    # 返回一个dict
    g.last_df = {order_book_id: history_bars(order_book_id, 1, '1d', 'close') for order_book_id in g.stocks}


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑
    sell_list = get_sell_list(context, g.bought_stocks_o)
    if len(sell_list) > 0:
        # log.info("to sell: %s" % sell_list)
        for security in sell_list:
            # profit = context.portfolio.positions[security].value - context.portfolio.positions[security].acc_avg_cost * \
            #          context.portfolio.positions[security].total_amount
            # user_log.info("Selling %s " % (security), "profit: %s" % profit,
            #          "init time %s" % context.portfolio.positions[security].init_time)
            order_target_value(security, 0)
            g.bought_stocks_o.remove(security)

    g.bought_num = len(context.portfolio.positions)
    if g.bought_num >= g.STOCKCOUNT:
        # log.info("bought num: %s, no need buy any more" % g.bought_num)
        return

    buy_list = get_buy_list(context, g.stocks, g.STOCKCOUNT)
    if len(buy_list) > 0:
        user_log.info("to buy list: %s" % buy_list)
        numtobuy = g.STOCKCOUNT - g.bought_num
        buy_cash = context.portfolio.cash / numtobuy
        for security in buy_list:
            todayclose = history_bars(security, 1, '1d', fields=['close'], include_now=True)
            if buy_cash < 100 * todayclose[0][0]:
                user_log.info("价格太贵，跳过 %s" % security)
                continue
            order_value(security, buy_cash)
            user_log.info("Buying %s" % (security))
            g.bought_stocks.append(security)
            g.bought_num += 1
            if g.bought_num >= g.STOCKCOUNT:
                break
    return


def after_trading(context):
    pass


# 获取卖票的列表
def get_sell_list(context, securitylist):
    listgot = []
    if len(securitylist) <= 0:
        return listgot

    for security in securitylist:
        prices = history_bars(security, 300, '1d', 'close')
        t_dif, t_dea, t_macd = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        yt_dif, yt_dea, yt_macd = talib.MACD(prices[:-2], fastperiod=12, slowperiod=26, signalperiod=9)

        todayclose = history_bars(security, 1, '1d', fields=['high', 'close'], include_now=True)
        #hisclose = history_bars(security, 21, unit='1d', fields=['close'], include_now=True)
        vols = history_bars(security, 21, '1d', fields='volume', include_now=True)
        #VOLT, MAVOL5, MAVOL10 = talib.VOL(securitylist, check_date=today, M1=5, M2=10, include_now=False)
        VOLT = vols[-1]
        MAVOL5 = np.mean(vols[-5:])
        MAVOL10 = np.mean(vols[-10:])

        # 涨跌幅小于6%，不动
        if todayclose[0][1] / context.portfolio.positions[security].avg_price <= 1.06 and \
                todayclose[0][1] / context.portfolio.positions[security].avg_price >= 0.94:
            continue
        if yt_macd[-1] >= 0 and t_macd[-1] < 0:  # 出现死叉
            listgot.append(security)
            user_log.info("%s 出现死叉" % security)
            continue
        elif todayclose[0][0] / todayclose[0][0] > 1.03:  # 当天回落超过3%
            if VOLT > MAVOL5:  # 放量回落
                listgot.append(security)
                user_log.info("%s 放量回落" % security)
                continue
            else:
                continue
        else:
            continue
    return listgot


# 获取买票的列表
def get_buy_list(context, securitylist, numtoget):
    numgot = -3  # 多找3个，以免有些买不进去
    listgot = []

    if numtoget <= 0 or len(securitylist) <= 0:
        return listgot

    for security in securitylist:
        prices = history_bars(security, 300, '1d', 'close', include_now=True)
        t_dif, t_dea, t_macd = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        yt_dif, yt_dea, yt_macd = talib.MACD(prices[:-2], fastperiod=12, slowperiod=26, signalperiod=9)
        yyt_dif, yyt_dea, yyt_macd = talib.MACD(prices[:-3], fastperiod=12, slowperiod=26, signalperiod=9)
        # 获取今天截止到现在的收盘价
        todayclose = history_bars(security, 1, '1d', fields='close', include_now=True)
        # 获取20日股价均值，不包括今天
        MA20 = np.mean(prices[-21:-1])
        # 获取当天成交量和过去5日成交量平均值
        #VOLT, MAVOL5, MAVOL10 = VOL(securitylist, check_date=today, M1=5, M2=10, include_now=False)
        vols = history_bars(security, 21, '1d', fields='volume', include_now=False)
        VOLT = vols[-1]
        MAVOL5 = np.mean(vols[-5:])
        MAVOL10 = np.mean(vols[-10:])

        if numgot >= numtoget:
            break
        if todayclose[0] < MA20:
            continue
        if VOLT < MAVOL5:
            continue

        # 出现红柱的第一天，可以买入
        if yt_macd[-1] < 0 and t_macd[-1] > 0:  # 出现金叉
            listgot.append(security)
            numgot += 1
            continue
        # 出现红柱的第二天，也可以买入
        elif yyt_macd[-1] < 0 and yt_macd[-1] >= 0 and t_macd[-1] > yt_macd[-1]:
            listgot.append(security)
            numgot += 1
            continue
            # 前天>昨天，昨天<今天，拐点出现
        elif yyt_macd[-1] > yt_macd[-1] and t_macd[-1] > yt_macd[-1]:
            listgot.append(security)
            numgot += 1
            continue
        else:
            continue

    return listgot


config = {
  "base": {
    "start_date": "2016-06-01",
    "end_date": "2021-06-01",
    "accounts": {
      "stock": 100000
    }
  },
  "extra": {
    "log_level": "verbose",
  },
  "mod": {
    "sys_analyser": {
            "enabled": True,
            "benchmark": "000300.XSHG",
            "plot": True
        },
    "sys_simulation": {
        "enabled": True,
        #"slippage":,
        #"commission-multiplier": ,
        # "matching_type": "last"
        },
  # "tushare": {
  #           "enabled": True
  #       }
  }
}

run_func(**globals())