#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-17 19:38

数据本地化方案
1. 更新方式分为两种：全量更新与增量更新
2. 考虑到 tushare 的查询接口太过简陋，同时考虑到查询限制，针对增量更新，作如下假设
    - 对 report_type = 1 的财务数据，更新从最新的两期财务报告期开始往后
    - 对 report_type = 5，11 的财务数据，增量更新时间为 report_type 最新一起财务报告期往前追溯 3 年
    - 对 report_type = 4 的财务数据，也是往前追溯 3 年
"""

import datetime
import time
from typing import List, Tuple, Union

import pandas as pd
import pymongo
import tushare as ts



