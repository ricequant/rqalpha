# -*- coding: utf-8 -*-

from rqalpha import run_file

config = {
  "base": {
    "start_date": "2016-06-01",
    "end_date": "2016-12-01",
    "securities": ['stock'],
    "stock_starting_cash": 100000,
    "benchmark": "000300.XSHG"
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

strategy_file_path = "./buy_and_hold.py"

run_file(strategy_file_path, config)
