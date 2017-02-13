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

from .future_portfolio import FuturePortfolio
from .stock_portfolio import StockPortfolio
from .base_portfolio import BasePortfolio
from ...const import ACCOUNT_TYPE


def init_portfolio(init_cash, start_date, account_type):
    if account_type == ACCOUNT_TYPE.STOCK:
        return StockPortfolio(init_cash, start_date, ACCOUNT_TYPE.STOCK)
    elif account_type == ACCOUNT_TYPE.FUTURE:
        return FuturePortfolio(init_cash, start_date, ACCOUNT_TYPE.FUTURE)
    elif account_type == ACCOUNT_TYPE.BENCHMARK:
        return StockPortfolio(init_cash, start_date, ACCOUNT_TYPE.BENCHMARK)