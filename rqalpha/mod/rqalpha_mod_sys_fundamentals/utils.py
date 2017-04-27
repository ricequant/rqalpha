# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import datetime as dt

import pandas as pd
import numpy as np


def parse_statdate(statDate):
    if statDate is None or type(statDate) != str or len(statDate) not in [4,6]:
        raise TypeError()
        
    quar2monthday = {
    1:(3,31),
    2:(6,30),
    3:(9,30),
    4:(12,31)
    }
    
    if len(statDate) == 4:
        statYear = int(statDate)
        statQuar = 4
    elif len(statDate) == 6:
        statYear = int(statDate[0:4])
        statQuar = int(statDate[-1:])
    
    return dt.date(statYear, quar2monthday[statQuar][0], quar2monthday[statQuar][1])
    

def parse_date(date):
    if type(date) == dt.date:
        return date
    elif type(date) == str:
        tokens = date.split('-')
        if len(tokens) != 3:
            raise TypeError()
        return dt.date(int(tokens[0]), int(tokens[1]), int(tokens[2]))
    
    raise TypeError()    
        