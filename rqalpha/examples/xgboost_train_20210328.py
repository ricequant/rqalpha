#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-28 10:16
"""
from collections import defaultdict

import tushare as ts

from rqalpha.data.data_proxy import DataProxy

import warnings

from rqalpha.data.base_data_source import BaseDataSource


warnings.filterwarnings("ignore")


from rqalpha.apis import *

#去除上市距beginDate不足n天的股票
# def delete_stop(stocks,beginDate,n):
#     stockList=[]
#     beginDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
#     for stock in stocks:
#         start_date=get_security_info(stock).start_date
#         if start_date<(beginDate-datetime.timedelta(days=n)).date():
#             stockList.append(stock)
#     return stockList

#剔除ST股
def delete_st(stocks,begin_date):
    st_data=ts.get_suspended().code
    stockList = [stock for stock in stocks if not st_data[stock][0]]
    return stockList

################################
# 2014年1月1日-2018年12月31日的5年区间。其中前4年区间（48个月）作为训练集，后1年区间（12个月）作为测试集。
#按月区间取值
peroid = 'M'
#样本区间（训练集+测试集的区间为2014-1-31到2018-12-31）
start_date = '2014-02-01'
start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d")
end_date = '2019-01-31'
end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d")
#训练集长度
train_length = 48
#聚宽一级行业


securities_list = ts.get_zz500s()
print(securities_list[:10])

data_source = BaseDataSource('/Users/jaxon/.rqalpha/bundle', {})
data_proxy = DataProxy(data_source, {})

import pickle
instruments = defaultdict(dict)

with open('/Users/jaxon/.rqalpha/bundle/instruments.pk', 'rb') as f:
    instrument = pickle.load(f)
    for d in instrument:
        instruments[d['order_book_id']] = d
    

def get_stock_list():
    stock_list = pd.read_csv("/data/db/stock_list.csv")['code'].str.replace(r'SH','XSHG')
    stock_list = stock_list.str.replace(r'SZ','XSHE')
    return list(stock_list)


def get_data(end_date):
    stock_data = pd.DataFrame()
    stock_list = get_stock_list()
    for stock_code in stock_list:
        try:
            open = data_proxy.history(stock_code, 160, '1d', 'open', end_date)
            close = data_proxy.history(stock_code, 160, '1d', 'close', end_date)
            high = data_proxy.history(stock_code, 160, '1d', 'high', end_date)
            low = data_proxy.history(stock_code, 160, '1d', 'low', end_date)
            volume = data_proxy.history(stock_code, 160, '1d', 'volume', end_date)
            data = pd.concat([open, high, low, close, volume], join='outer', axis=1)
            data.columns = ['open','high','low','close','volume']
            data['industry_code'] = instruments.get(stock_code)['industry_code']

            '''过去60个交易日日内真实波幅均值'''
            HIGH = data['high'].shift(1).iloc[1:]
            LOW = data['low'].shift(1).iloc[1:]
            CLOSE = data['close'].shift(1).iloc[1:]
            tmp = np.maximum(HIGH - LOW, np.abs(CLOSE.shift(1) - HIGH))
            TR = np.maximum(tmp, np.abs(CLOSE.shift(1) - LOW))
            data['ATR3M'] = TR.rolling(60).mean()

            '''过去20个交易日日内真实波幅均值'''
            HIGH = data['high'].shift(1).iloc[1:]
            LOW = data['low'].shift(1).iloc[1:]
            CLOSE = data['close'].shift(1).iloc[1:]

            tmp = np.maximum(HIGH - LOW, np.abs(CLOSE.shift(1) - HIGH))
            TR = np.maximum(tmp, np.abs(CLOSE.shift(1) - LOW))
            data['ATR1M'] = TR.rolling(20).mean()
            print(data.head(3))
            stock_data = pd.concat([stock_data, data])
        except Exception as e:
            print(stock_code, e)
            continue
    
    return stock_data


data = get_data(end_date)
print(data.head(3))




