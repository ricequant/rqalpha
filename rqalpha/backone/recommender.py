# coding: utf-8

from pyeasyga import pyeasyga
import numpy as np
import pandas as pd
import random, datetime


def create_individual(data):
    individual = data[:]
    random.shuffle(individual)
    return individual[0:10]




# define a fitness function
def fitness(individual, data):
    loss, inc, yesterday_close,restore_predicted,  = 0, 0, 0, 0
    avails, q = 0, 0
    counts = 0
    for selected, box in zip(individual, data):
        if selected:
            counts += 1
            #costs += box.get('cost')
            restore_predicted = box.get('restore_predicted')
            yesterday_close = box.get('yesterday_close')
            inc = box.get('inc')
            loss =float(box.get('loss')[1:-1])
            val_loss =float(box.get('val_loss')[1:-1])
            #print loss
            
            if loss <= 0.90 or loss >= 1.0:
                print loss
                return 0
            """
            if val_loss <= 0.90 or val_loss >= 1.0:
                print val_loss
                return 0            
            """
            
            if inc < 0 or inc > 1.0:
                print inc
                return 0
            
            
            q += loss *  inc

    if counts > 10:
        q = 0
    
    return q


if __name__=='__main__':
    today_str = "2018-08-07"
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    today = datetime.date.today().strftime("%Y%m%d")
    
    left = pd.DataFrame.from_csv('data%s/train_reslut%s.csv' % (today, today_str))
    right = pd.DataFrame.from_csv('data%s/predicted_reslut%s.csv' % (today, today_str))
    #print right
    #result = left.join(right, on='stock_id')
    result = pd.merge(left, right, on='stock_id')
    #print result
    
    result.to_csv ("merge_predicted_reslut%s.csv" % today_str, encoding="utf-8")
    result.to_csv ("data%s/merge_predicted_reslut%s.csv" % (today, today_str), encoding="utf-8")
    
    
    
    data = result.to_dict(orient='records')
    #ga = pyeasyga.GeneticAlgorithm(data)        # initialise the GA with data
    ga = pyeasyga.GeneticAlgorithm(data, population_size=100, mutation_probability=1, maximise_fitness=True)
    #ga = pyeasyga.GeneticAlgorithm(data, population_size=50, generations=100, crossover_probability=0.83, mutation_probability=0.02, elitism=False, maximise_fitness=True)
    #ga.population_size = 2000
    
    ga.fitness_function = fitness               # set the GA's fitness function
    ga.create_individual = create_individual
    ga.run()
    
    
    #print dir(ga)                                    # run the GA
    print ga.best_individual()                  # print the GA's best solution
    #print ga.seed_data
    print "--------"
    for individual in ga.last_generation():
        print individual
    
    
    print "------------------"
    print ga.best_individual()  
    
    
    
    
    