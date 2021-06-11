# -*- coding: utf-8 -*-
import datetime

from rqalpha.api import *
from rqalpha import run_func
from rqalpha.utils.logger import user_log

def init(context):
    logger.info("init")
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    context.fired = False

    context.slippage = 0.5


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        #order_percent(context.s1, 1)
        close = history_bars(context.s1, 1, '1d', 'close', adjust_type='post')
        user_log.debug(datetime.datetime.strftime(context.now, '%Y-%m-%d'), close)
        context.fired = True


config = {
  "base": {
    "start_date": "2021-05-06",
    "end_date": "2021-06-01",
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
# run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)

# 如果你的函数命名是按照 API 规范来，则可以直接按照以下方式来运行
run_func(**globals())
