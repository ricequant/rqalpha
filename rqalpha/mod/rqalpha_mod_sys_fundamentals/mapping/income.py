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
class income(base):
    __tablename__ = 'income'
        
    code    = Column(String, primary_key=True)
    pubDate = Column('pubdate', Date)
    statDate = Column('statdate', Date)    
              
    total_operating_revenue           =Column(Float)
    operating_revenue                 =Column(Float)
    interest_income                   =Column(Float)
    premiums_earned                   =Column(Float)
    commission_income                 =Column(Float)
    total_operating_cost              =Column(Float)
    operating_cost                    =Column(Float)
    interest_expense                  =Column(Float)
    commission_expense                =Column(Float)
    refunded_premiums                 =Column(Float)
    net_pay_insurance_claims          =Column(Float)
    withdraw_insurance_contract_reserve    =Column('withdraw_insurance_contract_re', Float)
    policy_dividend_payout            =Column(Float)
    reinsurance_cost                  =Column(Float)
    operating_tax_surcharges          =Column(Float)
    sale_expense                      =Column(Float)
    administration_expense            =Column(Float)
    financial_expense                 =Column(Float)
    asset_impairment_loss             =Column(Float)
    fair_value_variable_income        =Column(Float)
    investment_income                 =Column(Float)
    invest_income_associates          =Column(Float)
    exchange_income                   =Column(Float)
    operating_profit                  =Column(Float)
    non_operating_revenue             =Column(Float)
    non_operating_expense             =Column(Float)
    disposal_loss_non_current_liability    =Column('disposal_loss_non_current_liab', Float)
    total_profit                      =Column(Float)
    income_tax_expense                =Column(Float)
    net_profit                        =Column(Float)
    np_parent_company_owners          =Column(Float)
    minority_profit                   =Column(Float)
    basic_eps                         =Column(Float)
    diluted_eps                       =Column(Float)
    other_composite_income            =Column(Float)
    total_composite_income            =Column(Float)
    ci_parent_company_owners          =Column(Float)
    ci_minority_owners                =Column(Float)
    
    

