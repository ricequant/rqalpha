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

from rqalpha.const import ACCOUNT_TYPE

from .commission import StockCommission, FutureCommission
from .slippage import PriceRatioSlippage
from .tax import StockTax, FutureTax


class CommissionDecider(object):
    def __init__(self, multiplier):
        self.deciders = dict()
        self.deciders[ACCOUNT_TYPE.STOCK] = StockCommission(multiplier)
        self.deciders[ACCOUNT_TYPE.FUTURE] = FutureCommission(multiplier)

    def get_commission(self, account_type, trade):
        return self.deciders[account_type].get_commission(trade)


class SlippageDecider(object):
    def __init__(self, rate):
        self.decider = PriceRatioSlippage(rate)

    def get_trade_price(self, side, price):
        return self.decider.get_trade_price(side, price)


class TaxDecider(object):
    def __init__(self, rate=None):
        self.deciders = dict()
        self.deciders[ACCOUNT_TYPE.STOCK] = StockTax(rate)
        self.deciders[ACCOUNT_TYPE.BENCHMARK] = StockTax(rate)
        self.deciders[ACCOUNT_TYPE.FUTURE] = FutureTax(rate)

    def get_tax(self, account_type, trade):
        return self.deciders[account_type].get_tax(trade)
