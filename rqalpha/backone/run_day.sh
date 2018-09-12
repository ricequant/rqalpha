#!/bin/sh
# fetch data
rqalpha update_bundle
today = `date "+%Y%m%d"`
data_dir=data${today}
mkdir -p ${data_dir}/close_price
python fetch_all.py

# train LSTM
mkdir -p ${data_dir}weight_json_day
mkdir -p ${data_dir}weight_day

python lstm_train_all_by_day.py  ${today}
python predicted_next_day.py  ${today}

python recommender.py  ${today}

#back test


#sort

#send mail