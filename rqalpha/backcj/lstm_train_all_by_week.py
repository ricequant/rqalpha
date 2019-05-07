import time
import numpy as np
import os
import warnings
from numpy import newaxis
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.optimizers import RMSprop
from keras.models import Sequential
from eventlet import tpool
from keras import backend as K
from subprocess import call
from pandas import read_csv


def load_data(filename, seq_len, normalise_window):
    """
    f = open(filename, 'rb').read()
    data = f.decode().split('\n')
    """
    data = read_csv(filename)
    
    data = [x for x in data if str(x) != 'nan']
    sequence_length = seq_len + 5
    result = []
    
    for index in range(len(data) - sequence_length):
        a = data[index: index+seq_len]
        b = [data[index+sequence_length]]
        row = np.concatenate((a,b))
        #print row
        result.append(row)
    
    
    
    if normalise_window:
        result = normalise_windows(result)

    result = np.array(result)

    train = result
    np.random.shuffle(train)
    x_train = train[:, :-1]
    y_train = train[:, -1]

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    return [x_train, y_train]

def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data

def build_model(layers):
    model = Sequential()

    model.add(LSTM(
        input_shape=(layers[1], layers[0]),
        output_dim=layers[1],
        return_sequences=True))
    model.add(Dropout(0.2))

    model.add(LSTM(
        layers[2],
        return_sequences=False))
    model.add(Dropout(0.2))

    model.add(Dense(
        output_dim=layers[3]))
    model.add(Activation("softmax"))
    #model.add(Activation("linear"))

    start = time.time()
    model.compile(loss="mse", optimizer="rmsprop")
    #model.compile(loss='mean_squared_error', optimizer='adam')
    #model.compile(loss="mse", optimizer=RMSprop(lr=0.003, rho=0.9, epsilon=1e-06))
    print("> Compilation Time : ", time.time() - start)
    return model


def train_single_stock(filename, seq_len):
    global_start_time = time.time()
    epochs  = 1
    #seq_len = 50
    
    print filename
    data = read_csv('data_df/%s' % filename)
    print data
    if len(data) < 100:
        return False    
    
    
    X_train, y_train = load_data('data_df/%s' % filename, seq_len, True)
    
    print('> Data Loaded. Compiling...')
    model = build_model([1, seq_len, 100, 1])
    
    model.fit(
        X_train,
        y_train,
        batch_size=512,
        nb_epoch=epochs,
        validation_split=0.05)


    model.save_weights('weight_week/%s.h5' %  filename)
    model_json = model.to_json()
    with open('weight_json_week/%s.h5' %  filename, "w") as json_file:
        json_file.write(model_json)
    json_file.close()
    del model
    K.clear_session()
    """
    model.save('model/%s.h5' %  filename[:-4]) 
    model.reset_states()
    """
    print "Training duration (s) : %s  %s" % (time.time() - global_start_time, filename)

def get_all_order_book_id():
    all_order_book_id = []
    filepath = "close_price"
    files = os.listdir(filepath)
    for file in files:
        all_order_book_id.append(file)
    return all_order_book_id


if __name__=='__main__':
    all_stock_id = get_all_order_book_id()
    #print all_stock_id
    
    for stock_id in all_stock_id:
        model_file_path = 'weight_week/%s.h5' %  stock_id[:-4]
        #print model_file_path
        if not os.path.isfile(model_file_path):
            #call(["python", "train_single_stock.py", stock_id])
            train_single_stock(stock_id)
            #tpool.execute(train_single_stock, stock_id)
    
    
