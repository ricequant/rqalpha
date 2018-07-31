from rqalpha.backone.fetch_one import *
from rqalpha.backone.lstm_train_all_by_week import *
from rqalpha.backone.lstm_one_backtest import * 

#STOCKID = "002438.XSHG"
STOCKID = "600519.XSHG"
#STOCKID = "000670.XSHE"
seq_len = 30

config_dl = {
  "stock_id":STOCKID,
  "base": {
    "start_date": "2016-05-01",
    "end_date": "2018-03-01",
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

run_func(init=init_dl, before_trading=before_trading_dl, handle_bar=handle_bar_dl, end=end_dl, config=config_dl)

train_single_stock(STOCKID, seq_len)

config = {
  "stock_id":STOCKID,        
  "base": {
    "start_date": "2018-03-02",
    "end_date": "2018-06-03",
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