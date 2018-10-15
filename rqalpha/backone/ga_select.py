# coding: utf-8

from pyeasyga import pyeasyga
import datetime
import pandas as pd
import random
from operator import attrgetter
import sys

pd.set_option('display.height',1000)
pd.set_option('display.max_rows',500)
pd.set_option('display.max_columns',500)
pd.set_option('display.width',1000)







def create_individual(data):
    res =  [0 for _ in xrange(len(data))]
    return res

def crossover(parent_1, parent_2):
    crossover_index = random.randrange(1, len(parent_1))
    child_1 = parent_1[:crossover_index] + parent_2[crossover_index:]
    child_2 = parent_2[:crossover_index] + parent_1[crossover_index:]
    return child_1, child_2

# define a fitness function
def fitness(individual, data):
    costs, rise_fall_region_ratio, avails, counts, province, region, lower, q= 0, 0, 0, 0, 1, 1, 1, 0
    for selected, box in zip(individual, data):
        if selected:
            counts += 1
            rise_fall_region_ratio += box.get('rise_fall_region_ratio')
            inc = box.get('inc')
            if inc > 0.15:
                return 0
            if inc < 0.04:
                return 0
            yesterday_close = box.get('yesterday_close')
            restore_predicted = box.get('restore_predicted')
            if restore_predicted < yesterday_close:
                return 0
                
            q += rise_fall_region_ratio
            
            


    if counts > ga.count:
        q = 0
    
    return q

def selection(population):
    members = random.sample(population, 2)
    members.sort(key=attrgetter('fitness'), reverse=True)
    return members[0]


def mutate(individual):
    mutate_index = random.randrange(len(individual))
    if individual[mutate_index] == 0:
        individual[mutate_index] == 0
    else:
        individual[mutate_index] == 1


if __name__ == "__main__":

    print len(sys.argv)
    if len(sys.argv) == 2:
        now_time = datetime.datetime.strptime(sys.argv[1], "%Y%m%d")
        yesterday =  now_time.strftime("%Y-%m-%d")    
        
    
    else:
        today = datetime.date.today().strftime("%Y-%m-%d")
        yesterday = (datetime.date.today() -  datetime.timedelta(days=1)).strftime("%Y-%m-%d")    
    
    #today = "2018-09-29"
    filename = "top500/top500_%s" %  today
    df = pd.DataFrame.from_csv(filename)
    df = df.sort_values(by=['inc', 'rise_fall_ratio'], ascending=False)
    print df.head(500)
    data = df.head(500).to_dict(orient='records')
    
    data50 = []
    ga = pyeasyga.GeneticAlgorithm(data)        # initialise the GA with data
    ga.inc_ratio_limit = 0.5
    ga.rise_all_ratio_limit = 0.7
    ga.count = 50
    ga.fitness_function = fitness               # set the GA's fitness function
    ga.create_individual = create_individual
    ga.crossover_function = crossover
    #ga.mutate_function = mutate
    #ga.selection_function = selection    
    ga.run()
    print ga.best_individual()
    selected_list = ga.best_individual()[1]
    for selected, s in zip(selected_list, data):
        if selected:
            line = {"stock_id": s["stock_id"], "inc": s["inc"], "restore_predicted":s["restore_predicted"],"rise_fall":s["rise_fall"], "rise_fall_region": s["rise_fall_region"]}
            print "%s %s %s %s %s" % (s["stock_id"], s["inc"], s["restore_predicted"], s["rise_fall"],   s["rise_fall_region"])
            data50.append(line)
    df = pd.DataFrame(data50)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    today = datetime.date.today().strftime("%Y%m%d")
    df.to_csv ("recommder_result%s.csv" % (today_str), encoding="utf-8")
