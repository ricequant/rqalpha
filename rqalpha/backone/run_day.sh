#!/bin/sh
# fetch data
rqalpha update_bundle
rm -rf close_price
mkdir close_price
python fetch_all.py

# train LSTM
rm -rf weight_json_day
rm -rf weight_day
mkdir weight_json_day
mkdir weight_day

python lstm_train_all_by_day.py
python predicted_next_day.py

python recommender.py

#back test


#sort

#send mail