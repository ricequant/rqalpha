import lstm
import time
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split

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
    
    X_train, y_train, X_test, y_test = lstm.load_data('close_price/000001.XSHE.npy', seq_len, True)
    
    print('> Data Loaded. Compiling...')
    
    model = lstm.build_model([1, 50, 100, 1])
    
    model.fit(
        X_train,
        y_train,
        batch_size=512,
        nb_epoch=epochs,
        validation_split=0.05)
    
    #predictions = lstm.predict_sequences_multiple(model, X_test, seq_len, 50)
    #predicted = lstm.predict_sequence_full(model, X_test, seq_len)
    
    #model.save('my_model1.h5')
    
    model.save_weights('weight/000001.XSHE.h5')
    model_json = model.to_json()
    with open('weight_json/000001.XSHE.json', "w") as json_file:
        json_file.write(model_json)
    json_file.close()
    
    model.reset_states()
    
    #predicted = lstm.predict_point_by_point(model, X_test)        
    
    print('Training duration (s) : ', time.time() - global_start_time)
    #coef = np.corrcoef(predicted, y_test)
    #print coef
    #plot_results(predicted, y_test)
    #plot_results_multiple(predictions, y_test, 50)
    