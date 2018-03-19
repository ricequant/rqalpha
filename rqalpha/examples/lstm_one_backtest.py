# coding: utf-8
from rqalpha import run_func
from rqalpha.api import *
import talib
from sklearn.model_selection import train_test_split

import time
import warnings
import numpy as np
from numpy import newaxis
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential
import keras
from keras.models import load_model
from keras.models import model_from_json



"""
Bar(symbol: u'\u73e0\u6c5f\u94a2\u7434', order_book_id: u'002678.XSHE', datetime: datetime.datetime(2014, 1, 2, 0, 0), 
open: 7.08, close: 7.07, high: 7.14, low: 7.03, volume: 3352317.0, total_turnover: 23756852, limit_up: 7.78, limit_down: 6.36)


rqalpha run -f lstm_one_backtest.py -s 2017-01-09 -e 2018-3-09 -o result.pkl --plot --progress --account stock 10000

http://scikit-learn.org/stable/modules/preprocessing.html#standardization-or-mean-removal-and-variance-scaling

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

"""

#scheduler调用的函数需要包括context, bar_dict两个参数
def log_cash(context, bar_dict):
    logger.info("Remaning cash: %r" % context.portfolio.cash)
    """
    if context.is_buy_point:
        order = order_percent(context.s1, 1)
        if order:
            logger.info("----------下单成功 下单成功---------下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功----------买入价 %s" % order.avg_price)
            context.buy_price = order.avg_price
            context.buy = True
    
    if context.is_sell_point:
        order_target_value(context.s1, 0)
        logger.info("---------------清仓 --------清仓清仓清仓清仓清仓清仓-------清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓-------")
        context.buy = False
    """
    
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    context.s1 = context.config.stock_id
    #context.s1 = "002443.XSHE"
    context.s1_open_price = 0
    context.buy = False
    context.buy_price = 0
    
    context.is_buy_point = False
    context.is_sell_point = False
    context.is_stop_loss = False
    
    
    # 实时打印日志
    context.ORDER_PERCENT = 0.2
    context.restore_predicted = 0
    context.yesterday_close = 0
    context.s1_X = []
    context.s1_y = []
    
    context.predicted = False
    context.error = 0
    context.ok = 0    
    """
    context.model = load_model('model/%s.h5' % context.s1)
    context.model.compile(loss="mse", optimizer="rmsprop")
    """
    json_file = open("weight_json_week/%s.h5"% context.s1, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    context.model_by_week = model_from_json(loaded_model_json)
    context.model_by_week.load_weights("weight_week/%s.h5" % context.s1) 

    """
    json_file = open("weight_json/%s.h5"% context.s1, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    context.model = model_from_json(loaded_model_json)
    context.model.load_weights("weight/%s.h5" % context.s1) 
    """
    logger.info("RunInfo: {}".format(context.run_info))
    df = (all_instruments('CS'))
    context.all = df["order_book_id"]
    scheduler.run_weekly(log_cash, weekday=2)
    
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    logger.info("开盘前执行before_trading函数")
    
    history_close = history_bars(context.s1, 50, '1d', 'close')
    #logger.info(history_close)
    
    normalised_history_close = [((float(p) / float(history_close[0])) - 1) for p in history_close]
    
    normalised_history_close = np.array(normalised_history_close)
    normalised_history_close = normalised_history_close[newaxis,:]
    normalised_history_close = normalised_history_close[:,:,newaxis]
    
    predicted = context.model_by_week.predict(normalised_history_close)[0,0]
    
    normalised_history_close = [((float(p) / float(history_close[0])) - 1) for p in history_close]
    normalised_history_close.append(predicted)
    restore_normalise_window = [float(history_close[0]) * (float(p) + 1) for p in normalised_history_close]
    
    restore_predicted = restore_normalise_window[-1]
    context.restore_predicted = restore_predicted
    
    logger.info("yesterday %s   predict %s" % (history_close[-1], restore_predicted))
    context.yesterday_close = history_close[-1]
    
    if history_close[-1] < restore_predicted:
        logger.info("下星期涨---------下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨下星期涨--------")
        logger.info("yesterday %s   predict %s" % (history_close[-1], restore_predicted))
        context.is_buy_point = True
    else:
        context.is_buy_point = False
    
    
    if context.buy_price:
        if context.buy_price > history_close[-1] and  (context.buy_price - history_close[-1]) / context.buy_price > 0.10:
            
            logger.info(history_close[-1])
            logger.info(context.buy_price)
            logger.info((history_close[-1]  - context.buy_price) / context.buy_price)
            logger.info("------------fffffffffffff")
            context.is_stop_loss = True

    if context.buy_price:
        if context.buy_price < history_close[-1] and  ( history_close[-1] - context.buy_price) / context.buy_price > 0.08:
            
            logger.info(history_close[-1])
            logger.info(context.buy_price)
            logger.info((history_close[-1]  - context.buy_price) / context.buy_price)
            logger.info("------------fffffffffffff")
            context.is_stop_loss = True
    


def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data






# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    logger.info("每一个Bar执行")
    history_close = history_bars(context.s1, 1, '1d', 'close')
    logger.info("昨天天收盘价  %s" % context.yesterday_close)
    logger.info("今天收盘价  %s" % bar_dict[context.s1].close)
    logger.info("预测价一星期后 %s" % context.restore_predicted)
    logger.info("我股票的价 %s" % context.buy_price)
    
    logger.info("买点 %s" % context.is_buy_point)
    logger.info("卖点 %s" % context.is_sell_point)
    logger.info("止损 %s" % context.is_stop_loss)
    
    
    if context.buy_price:
        if context.buy_price < bar_dict[context.s1].close:
            logger.info("---------------赚-------哈哈哈------")
        else:
            logger.info("---------亏 ------------")
    else:
        logger.info("-----------没有股票-----------")
    
    if not context.buy:
        if context.is_buy_point:
            order = order_percent(context.s1, 1)
            if order:
                logger.info("----------下单成功 下单成功---------下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功下单成功----------买入价 %s" % order.avg_price)
                context.buy_price = order.avg_price
                context.buy = True        
    
    
    if context.buy and context.is_sell_point:
        order = order_target_value(context.s1, 0)
        if order:
            logger.info("---------------清仓 --------清仓清仓清仓清仓清仓清仓-------清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓清仓-------")
            context.buy = False
            context.is_sell_point = False
            context.buy_price = 0

    
    
    
    if context.is_stop_loss:
        order = order_target_value(context.s1, 0)
        if order:
            logger.info("---------------止损----------------止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损止损---")
            context.buy = False
            context.is_stop_loss = False
            context.buy_price = 0
    
    
    """
    if context.predicted and not context.buy and not is_suspended(context.s1):
        order = order_percent(context.s1, 1)
        if order:
            logger.info("买入价 %s" % order.avg_price)
            context.buy = True
    else:
        if context.buy and  not is_suspended(context.s1):
            order_target_value(context.s1, 0)
            context.buy = False
    """

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    logger.info("收盘后执行after_trading函数")
    
config = {
  "base": {
    "start_date": "2017-03-09",
    "end_date": "2018-03-09",
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

#run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)