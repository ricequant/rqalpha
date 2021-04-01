#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-28 09:11
"""

import numpy as np
import pandas as pd
from rqalpha.apis import *


class Factor():
    
    def calc(self, data):
        pass
    
    def calc_factors(self, data):
        data[self.name] = self.calc(data)
        return data
    

class EPTTM(Factor):
    """类型: 估值
    名称： 市盈率倒数 TTM
    公式: 归母净利润 TTM/总市值(Factor)
    """
    name = 'EPTTM'
    max_window = 1
    dependencies = ['pe_ratio']
    
    def calc(self, data):
        return (1 / data['pe_ratio']).iloc[0]


class SPTTM(Factor):
    """
    估值,
    市销率倒数 TTM,
    SPTTM,
    营业收入TTM/总市值(Factor)
    """
    name = 'SPTTM'
    max_window = 1
    dependencies = ['ps_ratio']
    
    def calc(self, data):
        return (1 / data['ps_ratio']).iloc[0]


class SUE0(Factor):
    """
    成长,
    标准化预期外盈利
    SUE,
    （单季度实际净利润-预期净利润）/预期净利润标准差(Factor)
    """
    '''含漂移项'''
    
    name = 'SUE0'
    max_window = 1
    
    global fields
    
    fields = [f'net_profit_{i}' if i != 0 else 'net_profit' for i in range(9)]
    
    dependencies = fields
    
    def calc(self, data):
        # 数据结构为 columns为 net_profit至net_profit_8
        df = pd.concat([v.T for v in data.values()], axis=1)
        df.columns = fields
        df.fillna(0, inplace=True)
        
        # 漂移项可以根据过去两年盈利同比变化Q{i,t} - Q{i,t-4}的均值估计
        # 数据结构为array
        tmp = df.iloc[:, 1:5].values - df.iloc[:, 5:].values
        
        C = np.mean(tmp, axis=1)  # 漂移项 array
        
        epsilon = np.std(tmp, axis=1)  # 残差项epsilon array
        
        Q = df.iloc[:, 4] + C + epsilon  # 带漂移项的季节性随机游走模型
        
        return (df.iloc[:, 0] - Q) / epsilon


class SUR0(Factor):
    """
    成长,
    标准化预期外收入,
    SUR,
    （单季度实际营业收入-预期营业收入）/预期营业收入标准差(Factor)
    """
    '''含漂移项'''
    
    name = 'SUR0'
    max_window = 1
    
    global fields
    
    fields = [f'operating_revenue_{i}' if i !=
                                          0 else 'operating_revenue' for i in range(9)]
    
    dependencies = fields
    
    def calc(self, data):
        # 数据结构为 columns为 net_profit至net_profit_8
        df = pd.concat([v.T for v in data.values()], axis=1)
        df.columns = fields
        df.fillna(0, inplace=True)
        
        # 漂移项可以根据过去两年盈利同比变化Q{i,t} - Q{i,t-4}的均值估计
        # 数据结构为array
        tmp = df.iloc[:, 1:5].values - df.iloc[:, 5:].values
        C = np.mean(tmp, axis=1)  # 漂移项 array
        epsilon = np.std(tmp, axis=1)  # 残差项epsilon array
        Q = df.iloc[:, 4] + C + epsilon  # 带漂移项的季节性随机游走模型
        return (df.iloc[:, 0] - Q) / epsilon


class DELTAROE(Factor):
    '''单季度净资产收益率-去年同期单季度净资产收益率'''
    
    name = 'DELTAROE'
    max_window = 1
    dependencies = ['roe', 'roe_4']
    
    def calc(self, data):
        return (data['roe'] - data['roe_4']).iloc[0]


class DELTAROA(Factor):
    '''单季度总资产收益率-去年同期单季度中资产收益率'''
    
    name = 'DELTAROA'
    max_window = 1
    dependencies = ['roa', 'roa_4']
    
    def calc(self, data):
        return (data['roa'] - data['roa_4']).iloc[0]


class ILLIQ(Factor):
    """
    流动性,
    非流动性冲击,
    ILLIQ,
    过去20个交易日涨幅绝对值/成交额均值(Factor)
    """
    name = 'ILLIQ'
    max_window = 21
    dependencies = ['close', 'money']
    
    def calc(self, data):
        abs_ret = np.abs(data['close'].pct_change().shift(1).iloc[1:])
        
        return (abs_ret / data['money'].iloc[1:]).mean()


class ATR1M(Factor):
    '''过去20个交易日日内真实波幅均值'''
    name = 'ATR1M'
    max_window = 22
    dependencies = ['close', 'high', 'low']
    
    def calc(self, data):
        HIGH = data['high'].shift(1).iloc[1:]
        LOW = data['low'].shift(1).iloc[1:]
        CLOSE = data['close'].shift(1).iloc[1:]
        
        tmp = np.maximum(HIGH - LOW, np.abs(CLOSE.shift(1) - HIGH))
        TR = np.maximum(tmp, np.abs(CLOSE.shift(1) - LOW))
        
        return TR.iloc[-20:].mean()


class ATR3M(Factor):
    '''过去60个交易日日内真实波幅均值'''
    name = 'ATR3M'
    max_window = 62
    dependencies = ['close', 'high', 'low']
    
    def calc(self, data):
        HIGH = data['high'].shift(1).iloc[1:]
        LOW = data['low'].shift(1).iloc[1:]
        CLOSE = data['close'].shift(1).iloc[1:]
        
        tmp = np.maximum(HIGH - LOW, np.abs(CLOSE.shift(1) - HIGH))
        TR = np.maximum(tmp, np.abs(CLOSE.shift(1) - LOW))
        
        return TR.iloc[-60:].mean()

def get_factor(order_book_ids, factors, start_date, end_date, universe, expect_df, data=None):
    """
    :param order_book_ids:
    :param factors:
    :param start_date:
    :param end_date:
    :param universe:
    :param expect_df:
    :return:
    """
    for order_book_id in order_book_ids:
        for factor in factors:
            factor_cls = globals()[factor]()
            fields = factor_cls.dependencies
            if not data:
                data = history_bars(order_book_id, 90, '1d', fields, start_date, end_date)
            data = factor_cls.calc_factors(data)
            

get_factor('000001.XSHE', ['ATR3M','ATR1M'], '20201101','20201105', '','')