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

from .benchmark_account import BenchmarkAccount
from .stock_account import StockAccount
from .future_account import FutureAccount
from .mixed_account import MixedAccount
from ...const import ACCOUNT_TYPE


def init_accounts(config):
    accounts = {}
    start_date = config.base.start_date
    total_cash = 0
    for account_type in config.base.account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            stock_starting_cash = config.base.stock_starting_cash
            accounts[ACCOUNT_TYPE.STOCK] = StockAccount(config, stock_starting_cash, start_date)
            total_cash += stock_starting_cash
        elif account_type == ACCOUNT_TYPE.FUTURE:
            future_starting_cash = config.base.future_starting_cash
            accounts[ACCOUNT_TYPE.FUTURE] = FutureAccount(config, future_starting_cash, start_date)
            total_cash += future_starting_cash
        else:
            raise NotImplementedError
    if config.base.benchmark is not None:
        accounts[ACCOUNT_TYPE.BENCHMARK] = BenchmarkAccount(config, total_cash, start_date)

    return accounts
