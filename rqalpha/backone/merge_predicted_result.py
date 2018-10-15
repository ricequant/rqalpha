# coding: utf-8

import pandas as pd
import os
import time
import datetime
from pyeasyga import pyeasyga

pd.set_option('display.height',1000)
pd.set_option('display.max_rows',500)
pd.set_option('display.max_columns',500)
pd.set_option('display.width',1000)

def date_compare(item1, item2):
    t1 = time.mktime(time.strptime(item1, '%Y-%m-%d'))
    t2 = time.mktime(time.strptime(item2, '%Y-%m-%d'))
    #print(t1, t2)
    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    else:
        return 0



def sort_files_by_date(base_dir):
    files_list = []
    date_key_list = []
    fs = os.listdir(base_dir)
    for f1 in fs:
        tmp_path = os.path.join(base_dir,f1)
        if not os.path.isdir(tmp_path):
            #print('文件: %s'%tmp_path)
            date_key = f1[-14:-4]
            date_key_list.append(date_key)
    q = sorted(date_key_list, date_compare)
    
    for date_key in q:
        files_name = "merge_predicted_result/merge_predicted_result%s.csv" % date_key
        files_list.append(files_name)
    return files_list
    
def sum_rise_fall(x, y):
    return x+y

def rise_fall_ok(x, count):
    return float(x) / count

def analyze_predicted_result(files):
    files_1 = files[:-1]
    files_2 = files[1:]
    result =pd.DataFrame([])
    count = 0
    for file1, file2 in zip(files_1, files_2):
        print file1
        print file2
        count = count + 1
        
        df = calculate_index(file1, file2)
        if not result.empty:
            tmp_df = pd.merge(result, df, on='stock_id')
            #print tmp_df
            tmp_df["rise_fall"] = tmp_df.apply(lambda row: sum_rise_fall(row['rise_fall_x'], row['rise_fall_y']), axis=1)
            tmp_df["rise_fall_region"] = tmp_df.apply(lambda row: sum_rise_fall(row['rise_fall_region_x'], row['rise_fall_region_y']), axis=1)
            #print tmp_df["rise_fall_sum"]
            result = tmp_df[["stock_id", "rise_fall", "rise_fall_region"]]
        else:
            result = df
            #print df
        #return []
        
    result["rise_fall_ratio"] = result.apply(lambda row: rise_fall_ok(row['rise_fall'], count), axis=1)
    result["rise_fall_region_ratio"] = result.apply(lambda row: rise_fall_ok(row['rise_fall_region'], count), axis=1)
    
    
    result = result.sort_values(by=['rise_fall_ratio'], ascending=False)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    result.to_csv("rise_fall/rf_%s" %  today,  encoding = "utf-8")
    return result

def recommeder_socket(predicted_result_index, today):

    to_day_predicted_reslut = "merge_predicted_result/merge_predicted_result%s.csv" % today
    to_day_rise_fall = "rise_fall/rf_%s" %  today
    today_df = pd.DataFrame.from_csv(to_day_predicted_reslut)
    rise_fall_df = pd.DataFrame.from_csv(to_day_rise_fall)
    
    df = pd.merge(today_df, rise_fall_df, on='stock_id')
    df = df.sort_values(by=['rise_fall_ratio'], ascending=False)
    return df



def compare_rise_fall_region(a, b):
    return abs(a-b)

def compare_rise_fall(predicted, close_x, close_y):

    a = close_x - close_y
    b = predicted - close_y
    a = int(a * 100)
    b = int(b * 100)
    if a > 0 and b > 0:
        return 1
    if a < 0 and b < 0:
        return 1
    if a == 0 and b ==  0:
        return 1
    return 0

def calculate_index(file1, file2):
    today_df = pd.DataFrame.from_csv(file1)
    tomorrow_df = pd.DataFrame.from_csv(file2)
    
    df = pd.merge(today_df, tomorrow_df, on='stock_id')
    #print df
    
    df['rise_fall'] = df.apply(lambda row: compare_rise_fall(row['restore_predicted_x'], row['yesterday_close_x'], row['yesterday_close_y']), axis=1)

    df['rise_fall_region'] = df.apply(lambda row: compare_rise_fall_region(row['restore_predicted_x'], row['yesterday_close_y']), axis=1)
    #print df[['restore_predicted_x', 'yesterday_close_x', 'yesterday_close_y', 'inc_x', 'rise_fall', 'rise_fall_region']]
    a = df[df['rise_fall'] == 1]['rise_fall'].count()
    b = df['rise_fall'].count()
    oneday_predicted_rise_fall_is_ok =  a / float(b)
    #print oneday_predicted_rise_fall_is_ok
    
    
    return df[["stock_id", "rise_fall", "rise_fall_region"]]
    
    left =  today_df[["stock_id","restore_predicted", "yesterday_close", "inc"]]
    right =  tomorrow_df[["stock_id","yesterday_close"]]
    
    result = pd.merge(left, right, on='stock_id')
    ddd =  result[["restore_predicted","yesterday_close_x","yesterday_close_y","inc"]]
    
    ddd["inc_check"] = ddd["yesterday_close_y"] - ddd["yesterday_close_x"] > 0
    ddd["inc_check2"] =  ddd["inc"] > 0
    ddd["result_1"] = ddd["inc_check2"] & ddd["inc_check"]
    
    
    """
    #print ddd[ddd["result_1"] == True].count() / ddd[ddd["inc_check"]== True].count()
    print ddd[ddd["result_1"] == True].count() / ddd[ddd["inc_check2"]== True].count()
    
    print ddd[ddd["result_1"] == True].count()
    print ddd[ddd["inc_check2"]== True].count()
    """

def calculate_index_test(file1, file2):
    today_df = pd.DataFrame.from_csv(file1)
    tomorrow_df = pd.DataFrame.from_csv(file2)
    
    left =  today_df[["stock_id","restore_predicted", "yesterday_close", "inc"]]
    right =  tomorrow_df[["stock_id","yesterday_close"]]
    
    result = pd.merge(left, right, on='stock_id')
    ddd =  result[["restore_predicted","yesterday_close_x","yesterday_close_y","inc"]]
    
    ddd["inc_check"] = ddd["yesterday_close_y"] - ddd["yesterday_close_x"] > 0
    ddd["inc_check2"] =  ddd["inc"] > 0
    ddd["result_1"] = ddd["inc_check2"] & ddd["inc_check"]
    
    #print ddd[ddd["result_1"] == True].count() / ddd[ddd["inc_check"]== True].count()
    print ddd[ddd["result_1"] == True].count() / ddd[ddd["inc_check2"]== True].count()
    
    print ddd[ddd["result_1"] == True].count()
    print ddd[ddd["inc_check2"]== True].count()


if __name__ == '__main__':
    base_dir = "merge_predicted_result"
    files = sort_files_by_date(base_dir)
    #print files
    
    predicted_result_index = analyze_predicted_result(files)
    #print predicted_result_index.head(500)

    today = datetime.date.today().strftime("%Y-%m-%d")
    #today = "2018-10-09"
        
    top500 = recommeder_socket(predicted_result_index, today)
    
    top500 =  top500.head(500)
    print top500[["yesterday_close", "restore_predicted", "rise_fall", "rise_fall_ratio", "rise_fall_region", "rise_fall_region_ratio"]]
    today = datetime.date.today().strftime("%Y-%m-%d")
    top500.to_csv("top500/top500_%s" %  today,  encoding = "utf-8")
    
    
    