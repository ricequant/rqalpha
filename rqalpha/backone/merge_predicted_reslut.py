# coding: utf-8

import pandas as pd
import os
import time


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
        files_name = "merge_predicted_reslut/merge_predicted_reslut%s.csv" % date_key
        files_list.append(files_name)
    return files_list
    

def analyze_predicted_result(files):
    files_1 = files[:-1]
    files_2 = files[1:]
    for file1, file2 in zip(files_1, files_2):
        print file1
        print file2
        calculate_index(file1, file2)
        
        
    return []

def recommeder_socket(predicted_result_index):
    return []

"""
单只股票指标分析， 
预测趋势正确率： 预测方向正确数 / 预测总天数  误差允许1%
预测正确范围偏差： 真实值和预测值的差绝对值的方差

全部股票总体：
预测趋势正确率： 方向正确数 / 预测总数  误差允许1%

"""
def calculate_index(file1, file2):
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
    base_dir = "merge_predicted_reslut"
    files = sort_files_by_date(base_dir)
    print files
    
    predicted_result_index = analyze_predicted_result(files)
    print predicted_result_index
    
    top50 = recommeder_socket(predicted_result_index)
    print top50
    
    