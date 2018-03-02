from rqalpha.api import *
import talib

"""
Bar(symbol: u'\u73e0\u6c5f\u94a2\u7434', order_book_id: u'002678.XSHE', datetime: datetime.datetime(2014, 1, 2, 0, 0), 
open: 7.08, close: 7.07, high: 7.14, low: 7.03, volume: 3352317.0, total_turnover: 23756852, limit_up: 7.78, limit_down: 6.36)


rqalpha run -f lstm.py -s 2014-01-01 -e 2018-01-01 --account stock 100000  --plot
"""

#scheduler调用的函数需要包括context, bar_dict两个参数
def log_cash(context, bar_dict):
    logger.info("Remaning cash: %r" % context.portfolio.cash)
    
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.s1 = "000001.XSHE"
    # 实时打印日志

    logger.info("RunInfo: {}".format(context.run_info))
    df = (all_instruments('CS'))
    context.all = df["order_book_id"]
    scheduler.run_weekly(log_cash, weekday=2)
    
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    logger.info("开盘前执行before_trading函数")

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    logger.info("每一个Bar执行")
    logger.info("打印Bar数据：")
    for s1 in context.all:
        #logger.info(bar_dict[s1])
        order_book_id = bar_dict[s1].order_book_id
        history_close = history_bars(order_book_id, 2000, '1d', 'close')
        if len(history_close) == 2000:
            info = "%s id: %s close: %s" % (bar_dict[s1].symbol,bar_dict[s1].order_book_id, bar_dict[s1].close)
            logger.info(info)
            
        
        #logger.info(history_bars(order_book_id, 50000, '1d', 'close'))

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    logger.info("收盘后执行after_trading函数")