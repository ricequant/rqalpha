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
class indicator(base):
    __tablename__ = 'indicator'
        
    code    = Column(String, primary_key=True)
    pubDate = Column('pubdate', Date)
    statDate = Column('statdate', Date)

    eps                                  =Column(Float)
    adjusted_profit                      =Column(Float)
    operating_profit                     =Column(Float)
    value_change_profit                  =Column(Float)
    roe                                  =Column(Float)
    inc_return                           =Column(Float)
    roa                                  =Column(Float)
    net_profit_margin                    =Column(Float)
    gross_profit_margin                  =Column(Float)
    expense_to_total_revenue             =Column(Float)
    operation_profit_to_total_revenue       =Column('operation_profit_to_total_reve',Float)
    net_profit_to_total_revenue          =Column(Float)
    operating_expense_to_total_revenue       =Column('operating_expense_to_total_rev',Float)
    ga_expense_to_total_revenue          =Column(Float)
    financing_expense_to_total_revenue       =Column('financing_expense_to_total_rev',Float)
    operating_profit_to_profit           =Column(Float)
    invesment_profit_to_profit           =Column(Float)
    adjusted_profit_to_profit            =Column(Float)
    goods_sale_and_service_to_revenue       =Column('goods_sale_and_service_to_reve',Float)
    ocf_to_revenue                       =Column(Float)
    ocf_to_operating_profit              =Column(Float)
    inc_total_revenue_year_on_year       =Column(Float)
    inc_total_revenue_annual             =Column(Float)
    inc_revenue_year_on_year             =Column(Float)
    inc_revenue_annual                   =Column(Float)
    inc_operation_profit_year_on_year       =Column('inc_operation_profit_year_on_y',Float)
    inc_operation_profit_annual          =Column(Float)
    inc_net_profit_year_on_year          =Column(Float)
    inc_net_profit_annual                =Column(Float)
    inc_net_profit_to_shareholders_year_on_year       =Column('inc_net_profit_to_shareholders',Float)
    inc_net_profit_to_shareholders_annual       =Column('inc_net_profit_to_shareholder2',Float)
