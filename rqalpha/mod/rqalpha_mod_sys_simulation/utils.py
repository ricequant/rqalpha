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

import six

from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.model.base_position import Positions
from rqalpha.model.portfolio import Portfolio
from rqalpha.model.base_account import BaseAccount
from rqalpha.utils.i18n import gettext as _


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    total_cash = 0

    if DEFAULT_ACCOUNT_TYPE.FUTURE.name in config.base.accounts and config.base.frequency != '1d':
        BaseAccount.AGGRESSIVE_UPDATE_LAST_PRICE = True

    for account_type, starting_cash in six.iteritems(config.base.accounts):
        if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
            if starting_cash == 0:
                raise RuntimeError(_(u"stock starting cash can not be 0, using `--account stock 100000`"))
            StockAccount = env.get_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
            StockPosition = env.get_position_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
            accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name] = StockAccount(starting_cash, Positions(StockPosition))
            total_cash += starting_cash
        elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
            if starting_cash == 0:
                raise RuntimeError(_(u"future starting cash can not be 0, using `--account future 100000`"))
            FutureAccount = env.get_account_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name)
            FuturePosition = env.get_position_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name)
            accounts[DEFAULT_ACCOUNT_TYPE.FUTURE.name] = FutureAccount(starting_cash, Positions(FuturePosition))
            total_cash += starting_cash
        else:
            raise NotImplementedError
    return Portfolio(start_date, 1, total_cash, accounts)
