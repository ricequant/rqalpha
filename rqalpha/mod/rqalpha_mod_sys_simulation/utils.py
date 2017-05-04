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
from rqalpha.model.account import StockAccount, FutureAccount
from rqalpha.model.position import Positions, StockPosition, FuturePosition
from rqalpha.model.portfolio import Portfolio
from rqalpha.utils.i18n import gettext as _


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    total_cash = 0
    for account_type in config.base.account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            stock_starting_cash = config.base.stock_starting_cash
            if stock_starting_cash == 0:
                raise RuntimeError(_(u"stock starting cash can not be 0, using `--stock-starting-cash 100000`"))
            accounts[ACCOUNT_TYPE.STOCK] = StockAccount(stock_starting_cash, Positions(StockPosition))
            total_cash += stock_starting_cash
        elif account_type == ACCOUNT_TYPE.FUTURE:
            future_starting_cash = config.base.future_starting_cash
            if future_starting_cash == 0:
                raise RuntimeError(_(u"future starting cash can not be 0, using `--future-starting-cash 100000`"))
            accounts[ACCOUNT_TYPE.FUTURE] = FutureAccount(future_starting_cash, Positions(FuturePosition))
            total_cash += future_starting_cash
        else:
            raise NotImplementedError
    return Portfolio(start_date, 1, total_cash, accounts)
