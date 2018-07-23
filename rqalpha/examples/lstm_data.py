from rqalpha.api import *
import talib
from rqalpha import run_func
import numpy as np
"""
Bar(symbol: u'\u73e0\u6c5f\u94a2\u7434', order_book_id: u'002678.XSHE', datetime: datetime.datetime(2014, 1, 2, 0, 0), 
open: 7.08, close: 7.07, high: 7.14, low: 7.03, volume: 3352317.0, total_turnover: 23756852, limit_up: 7.78, limit_down: 6.36)


rqalpha run -f lstm.py -s 2014-01-01 -e 2018-01-01 --account stock 100000  --plot

http://scikit-learn.org/stable/modules/preprocessing.html#standardization-or-mean-removal-and-variance-scaling

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

"""

#scheduler调用的函数需要包括context, bar_dict两个参数
def log_cash(context, bar_dict):
    logger.info("Remaning cash: %r" % context.portfolio.cash)
    
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.s1 = "000001.XSHE"
    # 实时打印日志
    
    context.X = []
    context.y = []

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
    
    history_close = history_bars(context.s1, 50, '1d', 'close')
    y = bar_dict[context.s1].close
    logger.info(bar_dict[context.s1].symbol)
    context.X.append(history_close)
    context.y.append(y)
    
    np.save("%s_X" % context.s1, np.array(context.X))
    np.save("%s_y" % context.s1, np.array(context.y))
    

    
    
    """
    for s1 in context.all:
        #logger.info(bar_dict[s1])
        order_book_id = bar_dict[s1].order_book_id
        history_close = history_bars(order_book_id, 2000, '1d', 'close')
        if len(history_close) == 90:
            info = "%s id: %s close: %s" % (bar_dict[s1].symbol,bar_dict[s1].order_book_id, bar_dict[s1].close)
            logger.info(type(history_close))
        
        #logger.info(history_bars(order_book_id, 50000, '1d', 'close'))
    """
# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    logger.info("收盘后执行after_trading函数")
    
   
config = {
  "base": {
    "start_date": "2004-06-01",
    "end_date": "2016-12-01",
    "benchmark": "000300.XSHG",
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
      "plot": True
    }
  }
}

# 您可以指定您要传递的参数
run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)

