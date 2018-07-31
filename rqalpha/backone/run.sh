#!/bin/sh
# fetch data
rqalpha update_bundle
rm -rf close_price
mkdir close_price
python fetch_all.py

# train LSTM
rm -rf weight_json_week
rm -rf weight_week
mkdir weight_json_week
mkdir weight_week

python lstm_train_all_by_week.py
python predicted_next_week.py

#back test


#sort

#send mail