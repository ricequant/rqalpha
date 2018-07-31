import lstm
import time
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
from keras.models import load_model
from numpy import newaxis


def plot_results(predicted_data, true_data):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    plt.plot(predicted_data, label='Prediction')
    plt.legend()
    plt.show()

def plot_results_multiple(predicted_data, true_data, prediction_len):
    fig = plt.figure(facecolor='white')
    ax = fig.add_subplot(111)
    ax.plot(true_data, label='True Data')
    #Pad the list of predictions to shift it in the graph to it's correct start
    for i, data in enumerate(predicted_data):
        padding = [None for p in range(i * prediction_len)]
        plt.plot(padding + data, label='Prediction')
        plt.legend()
    plt.show()


def load_test(filename, seq_len, normalise_window):
    """
    f = open(filename, 'rb').read()
    data = f.decode().split('\n')
    """
    data = np.load(filename)
    sequence_length = seq_len + 1
    result = []
    
    print  data
    print np.shape(data)
    for index in range(len(data) - sequence_length):
        result.append(data[index: index + sequence_length])
    
    
    if normalise_window:
        result = normalise_windows(result)

    result = np.array(result)


    x_test = result[:, :-1]
    y_test = result[:, -1]

    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))  

    return [x_test, y_test]

def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data


def predict_sequences_multiple(model, data, window_size, prediction_len):
    #Predict sequence of 50 steps before shifting prediction run forward by 50 steps
    prediction_seqs = []
    for i in range(int(len(data)/prediction_len)):
        curr_frame = data[i*prediction_len]
        predicted = []
        for j in range(prediction_len):
            predicted.append(model.predict(curr_frame[newaxis,:,:])[0,0])
            curr_frame = curr_frame[1:]
            curr_frame = np.insert(curr_frame, [window_size-1], predicted[-1], axis=0)
        prediction_seqs.append(predicted)
    return prediction_seqs

#Main Run Thread
if __name__=='__main__':
    global_start_time = time.time()
    epochs  = 1
    seq_len = 50
    
    print('> Loading data... ')
    
    
    """
    X = np.load("000001.XSHE_X.npy")
    y = np.load("000001.XSHE_y.npy")
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
    """
    
    X_test, y_test = load_test('000001.XSHE_y.npy', seq_len, True)
    
    print('> Data Loaded. Compiling...')
    
    model = load_model('my_model.h5')
    model.compile(loss="mse", optimizer="rmsprop")
    #predicted = model.predict(history_close)
    predictions = predict_sequences_multiple(model, X_test, seq_len, 50)
    #predicted = lstm.predict_sequence_full(model, X_test, seq_len)
    
    
    #predicted = lstm.predict_point_by_point(model, X_test)        
    
    print('Training duration (s) : ', time.time() - global_start_time)
    #coef = np.corrcoef(predicted, y_test)
    #print coef
    #plot_results(predicted, y_test)
    plot_results_multiple(predictions, y_test, 50)
    