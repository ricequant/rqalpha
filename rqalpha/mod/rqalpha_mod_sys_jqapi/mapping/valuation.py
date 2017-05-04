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
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import *
from sqlalchemy import Column, String, Integer, Float, Date
from sqlalchemy.orm import *
import pandas as pd

base = declarative_base()
class valuation(base):
    __tablename__ = 'valuation'
        
    code    = Column(String, primary_key=True)
    day     = Column(Date)

    capitalization            =Column(Float)
    circulating_cap           =Column(Float)
    market_cap                =Column(Float)
    circulating_market_cap    =Column(Float)
    turnover_ratio            =Column(Float)
    pe_ratio                  =Column(Float)
    pe_ratio_lyr              =Column(Float)
    pb_ratio                  =Column(Float)
    ps_ratio                  =Column(Float)
    pcf_ratio                 =Column(Float)    
    dividend_yield            =Column(Float)    
