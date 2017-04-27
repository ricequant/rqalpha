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
class balance(base):
    __tablename__ = 'balance'
        
    code    = Column(String, primary_key=True)
    pubDate = Column('pubdate', Date)
    statDate = Column('statdate', Date)

    cash_equivalents                      = Column(Float)
    settlement_provi                      = Column(Float)
    lend_capital                          = Column(Float)
    trading_assets                        = Column(Float)
    bill_receivable                       = Column(Float)
    account_receivable                    = Column(Float)
    advance_payment                       = Column(Float)
    insurance_receivables                 = Column(Float)
    reinsurance_receivables               = Column(Float)
    reinsurance_contract_reserves_receivable        = Column('reinsurance_contract_reserves_', Float)
    interest_receivable                   = Column(Float)
    dividend_receivable                   = Column(Float)
    other_receivable                      = Column(Float)
    bought_sellback_assets                = Column(Float)
    inventories                           = Column(Float)
    non_current_asset_in_one_year         = Column(Float)
    other_current_assets                  = Column(Float)
    total_current_assets                  = Column(Float)
    loan_and_advance                      = Column(Float)
    hold_for_sale_assets                  = Column(Float)
    hold_to_maturity_investments          = Column(Float)
    longterm_receivable_account           = Column(Float)
    longterm_equity_invest                = Column(Float)
    investment_property                   = Column(Float)
    fixed_assets                          = Column(Float)
    constru_in_process                    = Column(Float)
    construction_materials                = Column(Float)
    fixed_assets_liquidation              = Column(Float)
    biological_assets                     = Column(Float)
    oil_gas_assets                        = Column(Float)
    intangible_assets                     = Column(Float)
    development_expenditure               = Column(Float)
    good_will                             = Column(Float)
    long_deferred_expense                 = Column(Float)
    deferred_tax_assets                   = Column(Float)
    other_non_current_assets              = Column(Float)
    total_non_current_assets              = Column(Float)
    total_assets                          = Column(Float)
    shortterm_loan                        = Column(Float)
    borrowing_from_centralbank            = Column(Float)
    deposit_in_interbank                  = Column(Float)
    borrowing_capital                     = Column(Float)
    trading_liability                     = Column(Float)
    notes_payable                         = Column(Float)
    accounts_payable                      = Column(Float)
    advance_peceipts                      = Column(Float)
    sold_buyback_secu_proceeds            = Column(Float)
    commission_payable                    = Column(Float)
    salaries_payable                      = Column(Float)
    taxs_payable                          = Column(Float)
    interest_payable                      = Column(Float)
    dividend_payable                      = Column(Float)
    other_payable                         = Column(Float)
    reinsurance_payables                  = Column(Float)
    insurance_contract_reserves           = Column(Float)
    proxy_secu_proceeds                   = Column(Float)
    receivings_from_vicariously_sold_securities        = Column('receivings_from_vicariously_so', Float)
    non_current_liability_in_one_year        = Column('non_current_liability_in_one_y', Float)
    other_current_liability               = Column(Float)
    total_current_liability               = Column(Float)
    longterm_loan                         = Column(Float)
    bonds_payable                         = Column(Float)
    longterm_account_payable              = Column(Float)
    specific_account_payable              = Column(Float)
    estimate_liability                    = Column(Float)
    deferred_tax_liability                = Column(Float)
    other_non_current_liability           = Column(Float)
    total_non_current_liability           = Column(Float)
    total_liability                       = Column(Float)
    paidin_capital                        = Column(Float)
    capital_reserve_fund                  = Column(Float)
    treasury_stock                        = Column(Float)
    specific_reserves                     = Column(Float)
    surplus_reserve_fund                  = Column(Float)
    ordinary_risk_reserve_fund            = Column(Float)
    retained_profit                       = Column(Float)
    foreign_currency_report_conv_diff        = Column('foreign_currency_report_conv_d', Float)
    equities_parent_company_owners        = Column(Float)
    minority_interests                    = Column(Float)
    total_owner_equities                  = Column(Float)
    total_sheet_owner_equities            = Column(Float)
    

