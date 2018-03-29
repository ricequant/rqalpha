from rqalpha.backcj.fetch_one import *
from rqalpha.backcj.lstm_train_all_by_week import *
from rqalpha.backcj.lstm_one_backtest import * 

STOCKID = "600560.XSHG"
seq_len = 30

config_dl = {
  "stock_id":STOCKID,
  "base": {
    "start_date": "2008-04-01",
    "end_date": "2017-10-01",
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

train_single_stock(STOCKID, seq_len)

config = {
  "stock_id":STOCKID,        
  "base": {
    "start_date": "2017-04-09",
    "end_date": "2017-06-09",
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

#run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)