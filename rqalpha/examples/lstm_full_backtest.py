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


"""
Bar(symbol: u'\u73e0\u6c5f\u94a2\u7434', order_book_id: u'002678.XSHE', datetime: datetime.datetime(2014, 1, 2, 0, 0), 
open: 7.08, close: 7.07, high: 7.14, low: 7.03, volume: 3352317.0, total_turnover: 23756852, limit_up: 7.78, limit_down: 6.36)

rqalpha run -f lstm_full_backtest.py -s 2017-01-01 -e 2017-03-01 --account stock 100000  --plot

"""

#scheduler调用的函数需要包括context, bar_dict两个参数
def log_cash(context, bar_dict):
    logger.info("Remaning cash: %r" % context.portfolio.cash)
    
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # 在context中保存全局变量
    
    context.error = 0
    context.ok = 0    

    context.model = load_model('my_model.h5')
    context.model.compile(loss="mse", optimizer="rmsprop")

    logger.info("RunInfo: {}".format(context.run_info))
    df = (all_instruments('CS'))
    context.all = df["order_book_id"]
    scheduler.run_weekly(log_cash, weekday=2)
    
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    logger.info("开盘前执行before_trading函数")


def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    logger.info("每一个Bar执行")
    logger.info("打印Bar数据：")
    
    logger.info("stock count %s" %  len(context.all))
    for s1 in context.all:
        #logger.info(bar_dict[s1])
        order_book_id = bar_dict[s1].order_book_id
    
        history_close = history_bars(order_book_id, 51, '1d', 'close')
        history_close = history_close[:-1]
        if len(history_close) != 50:
            continue
        
        y = bar_dict[order_book_id].close
        
        yesterday_close = history_close[-2]
        
        
        normalised_history_close = [((float(p) / float(history_close[0])) - 1) for p in history_close]
        
        print history_close
        print normalised_history_close
        
        normalised_history_close = np.array(normalised_history_close)
        normalised_history_close = normalised_history_close[newaxis,:]
        normalised_history_close = normalised_history_close[:,:,newaxis]
        
        predicted = context.model.predict(normalised_history_close)[0,0]
        
        normalised_history_close = [((float(p) / float(history_close[0])) - 1) for p in history_close]
        normalised_history_close.append(predicted)
        restore_normalise_window = [float(history_close[0]) * (float(p) + 1) for p in normalised_history_close]
        
        restore_predicted = restore_normalise_window[-1]
        logger.info("predicted: %s yesterday_close:%s restore_predicted:%s real: %s" %  (predicted,yesterday_close, restore_predicted, y))
        
        flag = 0
        if yesterday_close > y and yesterday_close > restore_predicted:
            context.ok = context.ok + 1
            flag = flag + 1
        if yesterday_close < y and yesterday_close < restore_predicted:
            context.ok = context.ok + 1
            flag = flag + 1
        
        if not flag:
            context.error  = context.error + 1
            
        logger.info("--eve----------------------------------------------")
        logger.info("stock count %s" %  len(context.all))
        logger.info("error:%s  ok:%s ratio:%s" % (context.error, context.ok, round(float(context.ok)/(context.error + context.ok), 2)))
        logger.info("--eve   -------------------------------------------")
    


# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    logger.info("收盘后执行after_trading函数")