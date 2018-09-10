import pandas as pd

if __name__ == '__main__':
    today_df = pd.DataFrame.from_csv('merge_predicted_reslut/merge_predicted_reslut2018-09-04.csv')
    tomorrow_df = pd.DataFrame.from_csv('merge_predicted_reslut/merge_predicted_reslut2018-09-05.csv')
    
    left =  today_df[["stock_id","restore_predicted", "yesterday_close", "inc"]]
    right =  tomorrow_df[["stock_id","yesterday_close"]]
    
    result = pd.merge(left, right, on='stock_id')
    ddd =  result[["restore_predicted","yesterday_close_x","yesterday_close_y","inc"]]
    
    ddd["inc_check"] = ddd["yesterday_close_y"] - ddd["yesterday_close_x"] > 0
    ddd["inc_check2"] =  ddd["inc"] > 0
    ddd["result_1"] = ddd["inc_check2"] & ddd["inc_check"]
    
    print ddd[ddd["result_1"] == True].count() / ddd[ddd["inc_check2"]== True].count()
    
    print ddd[ddd["result_1"] == True].count()
    print ddd[ddd["inc_check2"]== True].count()