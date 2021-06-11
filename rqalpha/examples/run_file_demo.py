# -*- coding: utf-8 -*-

from rqalpha import run_file

config = {
  "base": {
    "start_date": "2016-06-01",
    "end_date": "2016-12-01",
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
            "benchmark": "000300.XSHG",
            "plot": True
        },
    "sys_simulation": {
            "enabled": True,
            # "matching_type": "last"
        },
  "tushare": {
            "enabled": True
        }
  }
}

strategy_file_path = "./macd.py"

run_file(strategy_file_path, config)
