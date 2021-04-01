#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-29 17:15
"""

from rqalpha.apis import *



config = {
  "base": {
    "start_date": "2016-06-01",
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
    },
    "sys_simulation": {
        "enabled": True,
        "slippage": 0.001
    }
  }
}

def init(context):
    context.dapan_threshold =0
    context.niu_signal = 1  # 牛市就上午开仓，熊市就下午
    context.ETF_list = {
  
      '399905.XSHE': '159902.XSHE',  # 中小板指
      '399632.XSHE': '159901.XSHE',  # 深100etf
      '000016.XSHG': '510050.XSHG',  # 上证50
      '000010.XSHG': '510180.XSHG',  # 上证180
  
      '000852.XSHG': '512100.XSHG',  # 中证1000etf
      '399295.XSHE': '159966.XSHE',  # 创蓝筹
      '399958.XSHE': '159967.XSHE',  # 创成长
      '000015.XSHG': '510880.XSHG',  # 红利ETF
      '399324.XSHE': '159905.XSHE',  # 深红利
      '399006.XSHE': '159915.XSHE',  # 创业板
      '000300.XSHG': '510300.XSHG',  # 沪深300
      '000905.XSHG': '510500.XSHG',  # 中证500
      '399673.XSHE': '159949.XSHE',  # 创业板50
      '000688.XSHG': '588000.XSHG'  # 科创50
    }
    
    
  
  


