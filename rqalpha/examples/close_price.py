# coding: utf-8

from rqalpha.api import *
import talib
from rqalpha import run_func
import numpy as np
import datetime
"""
Bar(symbol: u'\u73e0\u6c5f\u94a2\u7434', order_book_id: u'002678.XSHE', datetime: datetime.datetime(2014, 1, 2, 0, 0), 
open: 7.08, close: 7.07, high: 7.14, low: 7.03, volume: 3352317.0, total_turnover: 23756852, limit_up: 7.78, limit_down: 6.36)


rqalpha run -f lstm.py -s 2014-01-01 -e 2018-01-01 --account stock 100000  --plot

http://scikit-learn.org/stable/modules/preprocessing.html#standardization-or-mean-removal-and-variance-scaling

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)



rqalpha run -f get_day_close_price.py -s 2000-01-01 -e 2017-01-01 -o result.pkl --plot --progress --account stock 10000




"""




    
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.all_close_price = {}
    context.today = None
    
    logger.info("RunInfo: {}".format(context.run_info))
    #df = (all_instruments('CS'))
    #context.all = df["order_book_id"]
    
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    logger.info("开盘前执行before_trading函数")

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    logger.info("每一个Bar执行")
    logger.info("打印Bar数据：")
    
    """
    
    history_close = history_bars(context.s1, 50, '1d', 'close')
    y = bar_dict[context.s1].close
    logger.info(bar_dict[context.s1].symbol)
    context.X.append(history_close)
    context.y.append(y)
    
    np.save("%s_X" % context.s1, np.array(context.X))
    
    np.save("%s_y" % context.s1, np.array(context.y))
    
    """
    
    df = (all_instruments('CS'))
    all = df["order_book_id"]    
    
    for s1 in all:
        #logger.info(bar_dict[s1])
        order_book_id = bar_dict[s1].order_book_id
        #history_close = history_bars(order_book_id, 50, '1d', 'close')
        info = "%s id: %s close: %s" % (bar_dict[s1].symbol,bar_dict[s1].order_book_id, bar_dict[s1].close)
        #logger.info(info)
        name = bar_dict[s1].symbol
        id = bar_dict[s1].order_book_id
        close_price = bar_dict[s1].close
        
        if context.all_close_price.get(id, []):
            context.all_close_price[id].append(close_price)
        else:
            context.all_close_price[id] = [close_price]
        
        context.today = bar_dict[s1].datetime
        
   
   
    """
    b = context.today.strftime("%Y-%m-%d")
    logger.info("%s  %s" % (config["base"]["end_date"],b))
    if config["base"]["end_date"] == b:
        for book_id, data in context.all_close_price.items():
            np.save("close_price/%s" % book_id, np.array(data))
    """
        
# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    logger.info("收盘后执行after_trading函数")


def end(context):
    logger.info("用户程序执行完成")
    for book_id, data in context.all_close_price.items():
        np.save("close_price/%s" % book_id, np.array(data))   

config = {
  "base": {
    "start_date": "2004-06-01",
    "end_date": "2017-02-01",
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
run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, end=end, config=config)


