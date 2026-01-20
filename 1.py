from rqalpha.apis import *
from rqalpha import run_func
from datetime import date
 
c = {
    "base": {
        "start_date": "2023-06-20",
        "end_date": "2023-07-10",
        'frequency': '1d',
        "init_positions": "688768.XSHG:1445",
        # 账户设置，默认为空；key 为账户类型，值为账户初始资金
        "accounts": {
            # 股票账户，下属资产包括股票、基金、可转债和沪深两市的期权等
            "STOCK": 1000000,
        },
        # 初始化仓位,格式参考 000001.XSHE:1000,IF1701:-1
        # 是否开启期货历史交易参数进行回测
        "futures_time_series_trading_parameters": True,
    },
    "mod":{
        "sys_analyser": {
            "benchmark": "000300.XSHG",
            # "plot": True,
        },
    }
}
 
 
def init(context):
    pass
 
 
def handle_bar(context, bar_dict):
    pass
 
def after_trading(context):
    print(get_position('688768.XSHG').quantity)
 
 
run_func(config=c, init=init, handle_bar=handle_bar, after_trading=after_trading)
