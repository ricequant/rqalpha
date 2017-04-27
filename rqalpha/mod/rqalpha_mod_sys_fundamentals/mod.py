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

import pandas as pd
import numpy as np

from rqalpha.interface import AbstractMod
from rqalpha.environment import Environment
from rqalpha.events import EVENT

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import *
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import *
from sqlalchemy import func

from mapping import *
from utils import *

# todo: 可配置
engine=create_engine('oracle://CJHJDM:CJHJDM@172.16.48.205:1521/cjhjdm', echo=False) 
#engine=create_engine('sqlite://///home/db_fund', echo=False) 
Session = sessionmaker(bind=engine)
session = Session()
    
"""
    完全按照聚宽实现，参见：https://www.joinquant.com/api#get_fundamentals
"""
def get_fundamentals(query_object, date=None, statDate=None):
         
    if date is not None and statDate is not None:
        raise TypeError()

    if date is not None:
        date = parse_date(date)                       
        
    if statDate is not None:            
        statDate = parse_statdate(statDate)
        # debug
        print (statDate)
    
    # 如果都为None，取date
    if date is None and statDate is None:
        date = dt.date.today()-dt.timedelta(1)
    
    # add filter
    q = query_object        
    first_entity = None
    visited_entity = []
    for des in query_object.column_descriptions:
        entity = des['entity']
        if entity in visited_entity:
            continue
        
        # filt code
        if first_entity is None:
            first_entity = entity
        else:
            q = q.filter(first_entity.code == entity.code)
        
        # filt date
        if entity == valuation:
            if statDate is not None:
                q = q.filter(entity.day == statDate)
            else:
                q1 = Query([entity.code, func.max(entity.day).label('day')]).filter(entity.day<=date).group_by(entity.code).subquery()
                q = q.filter(entity.day <= date).filter(entity.day == q1.c.day, entity.code == q1.c.code)                
                
        elif entity in [balance,cash_flow,income,indicator]:                        
            if statDate is not None:
                q = q.filter( entity.statDate == statDate )
            else:
                q1 = Query([entity.code, func.max(entity.pubDate).label('pubDate')]).filter(entity.pubDate<=date).group_by(entity.code).subquery()                
                q = q.filter(entity.pubDate <= date).filter(entity.pubDate == q1.c.pubDate, entity.code == q1.c.code)                
        else:
            raise TypeError()
            
        visited_entity.append(entity)
                
    df = pd.read_sql_query(q.statement, engine)
            
    return df 
    
    
def query(*args, **kwargs):
    return Query(args)


class FundamentalsAPIMod(AbstractMod):
    def start_up(self, env, mod_config):                    
        
        from rqalpha.api.api_base import register_api
        # api
        register_api('get_fundamentals', get_fundamentals)
        register_api('query', query)
        # model
        register_api('income', income)
        register_api('balance', balance)
        register_api('cash_flow', cash_flow)
        register_api('indicator', indicator)
        register_api('valuation', valuation)
               
    def tear_down(self, code, exception=None):
        pass
        