from rqalpha.backone.fetch_one import *
from rqalpha.backone.lstm_train_all_by_day import *
from rqalpha.backone.predicted_next_day import * 
import datetime

#STOCKID = "002438.XSHG"
STOCKID = "600519.XSHG"
#STOCKID = "000670.XSHE"
seq_len = 30
result = {}

before_yesterday = (datetime.date.today() -  datetime.timedelta(days=1)).strftime("%Y-%m-%d")
yesterday = (datetime.date.today() -  datetime.timedelta(days=1)).strftime("%Y-%m-%d")
today = datetime.date.today().strftime("%Y-%m-%d")
print before_yesterday
print yesterday

config_dl = {
  "stock_id":STOCKID,
  "base": {
    "start_date": yesterday,
    "end_date": today,
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

run_func(init=init_dl, before_trading=before_trading_dl, handle_bar=handle_bar_dl, config=config_dl)

train_single_stock("%s.npy" % STOCKID, result)



predicted_one = True
config = {
  "stock_id":STOCKID,
  "predicted_one":predicted_one,
  "base": {
    "start_date":yesterday,
    "end_date": today,
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
    

run_func(init=init_next_day, before_trading=before_trading_next_day, handle_bar=handle_bar_next_day, config=config)
"""
json_file = open("weight_json_day/%s.npy.h5"% STOCKID, 'r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)
model.load_weights("weight_day/%s.npy.h5" % STOCKID) 

normalised_history_close = np.array([[[ 0.07396154],[ 0.09833347],[ 0.0984876 ],[ 0.09906536],[ 0.09991453],[ 0.10092786],[ 0.10203195],[ 0.10317754],[ 0.10433278],[ 0.10547726],[ 0.10659847],[ 0.107689  ],[ 0.10874482],[ 0.10976392],[ 0.11074561],[ 0.11169007],[ 0.112598  ],[ 0.11347043],[ 0.11430836],[ 0.11511308],[ 0.11588572],[ 0.1166276 ],[ 0.11733988],[ 0.11802375],[ 0.11868031],[ 0.11931065],[ 0.11991578],[ 0.12049671],[ 0.12105443],[ 0.12158989],[ 0.12210394],[ 0.12259747],[ 0.12307128],[ 0.12352616],[ 0.12396284],[ 0.12438206],[ 0.1247845 ],[ 0.12517075],[ 0.12554161],[ 0.12589762],[ 0.12623931],[ 0.12656738],[ 0.12688226],[ 0.12718451],[ 0.12747471],[ 0.12775323],[ 0.12802061],[ 0.12827721],[ 0.1285236 ],[ 0.12876013]]])
predicted_result = model.predict(normalised_history_close)
print predicted_result
"""
