import os
import re

if __name__ == '__main__':
    
    fs = os.listdir("merge_predicted_result")
    for file_name in fs:
        new_name = file_name.replace("reslut", "result")
        os.rename("merge_predicted_result/%s" % file_name, "merge_predicted_result/%s" % new_name)