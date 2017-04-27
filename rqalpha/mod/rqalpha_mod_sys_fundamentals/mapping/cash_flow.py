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
class cash_flow(base):
    __tablename__ = 'cash_flow'
        
    code    = Column(String, primary_key=True)
    pubDate = Column('pubdate', Date)
    statDate = Column('statdate', Date)

    goods_sale_and_service_render_cash       = Column('goods_sale_and_service_render_', Float)
    net_deposit_increase                 = Column(Float)
    net_borrowing_from_central_bank       = Column('net_borrowing_from_central_ban', Float)
    net_borrowing_from_finance_co        = Column(Float)
    net_original_insurance_cash          = Column(Float)
    net_cash_received_from_reinsurance_business       = Column('net_cash_received_from_reinsur', Float)
    net_insurer_deposit_investment       = Column(Float)
    net_deal_trading_assets              = Column(Float)
    interest_and_commission_cashin       = Column(Float)
    net_increase_in_placements           = Column(Float)
    net_buyback                          = Column(Float)
    tax_levy_refund                      = Column(Float)
    other_cashin_related_operate         = Column(Float)
    subtotal_operate_cash_inflow         = Column(Float)
    goods_and_services_cash_paid         = Column(Float)
    net_loan_and_advance_increase        = Column(Float)
    net_deposit_in_cb_and_ib             = Column(Float)
    original_compensation_paid           = Column(Float)
    handling_charges_and_commission       = Column('handling_charges_and_commissio', Float)
    policy_dividend_cash_paid            = Column(Float)
    staff_behalf_paid                    = Column(Float)
    tax_payments                         = Column(Float)
    other_operate_cash_paid              = Column(Float)
    subtotal_operate_cash_outflow        = Column(Float)
    net_operate_cash_flow                = Column(Float)
    invest_withdrawal_cash               = Column(Float)
    invest_proceeds                      = Column(Float)
    fix_intan_other_asset_dispo_cash       = Column('fix_intan_other_asset_dispo_ca',Float)
    net_cash_deal_subcompany             = Column(Float)
    other_cash_from_invest_act           = Column(Float)
    subtotal_invest_cash_inflow          = Column(Float)
    fix_intan_other_asset_acqui_cash       = Column('fix_intan_other_asset_acqui_ca',Float)
    invest_cash_paid                     = Column(Float)
    impawned_loan_net_increase           = Column(Float)
    net_cash_from_sub_company            = Column(Float)
    other_cash_to_invest_act             = Column(Float)
    subtotal_invest_cash_outflow         = Column(Float)
    net_invest_cash_flow                 = Column(Float)
    cash_from_invest                     = Column(Float)
    cash_from_mino_s_invest_sub          = Column(Float)
    cash_from_borrowing                  = Column(Float)
    cash_from_bonds_issue                = Column(Float)
    other_finance_act_cash               = Column(Float)
    subtotal_finance_cash_inflow         = Column(Float)
    borrowing_repayment                  = Column(Float)
    dividend_interest_payment            = Column(Float)
    proceeds_from_sub_to_mino_s          = Column('proceeds_from_sub_to_mino_s',Float)
    other_finance_act_payment            = Column(Float)
    subtotal_finance_cash_outflow        = Column(Float)
    net_finance_cash_flow                = Column(Float)
    exchange_rate_change_effect          = Column(Float)
    cash_equivalent_increase             = Column(Float)
    cash_equivalents_at_beginning        = Column(Float)
    cash_and_equivalents_at_end          = Column(Float)

