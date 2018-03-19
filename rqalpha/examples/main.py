from rqalpha.examples.fetch_one import *
from rqalpha.examples.lstm_train_all_by_week import *
from rqalpha.examples.lstm_one_backtest import * 

STOCKID = "600386.XSHE"


config_dl = {
  "stock_id":STOCKID,
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
      "plot": False
    }
  }
}

#run_func(init=init_dl, before_trading=before_trading_dl, handle_bar=handle_bar_dl, end=end_dl, config=config_dl)

train_single_stock(STOCKID)

config = {
  "stock_id":STOCKID,        
  "base": {
    "start_date": "2016-01-09",
    "end_date": "2017-01-09",
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

run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)