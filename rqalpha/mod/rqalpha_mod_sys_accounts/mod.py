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


from rqalpha.interface import AbstractMod
from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha import export_as_api

from .account_model import StockAccount, FutureAccount, BenchmarkAccount
from .position_model import StockPosition, FuturePosition
from .api import api_future, api_stock


class AccountMod(AbstractMod):

    def start_up(self, env, mod_config):

        StockPosition.stock_t1 = mod_config.stock_t1

        # 注入 Account
        env.set_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name, StockAccount)
        env.set_account_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name, FutureAccount)
        env.set_account_model(DEFAULT_ACCOUNT_TYPE.BENCHMARK.name, BenchmarkAccount)

        # 注入 Position
        env.set_position_model(DEFAULT_ACCOUNT_TYPE.STOCK.name, StockPosition)
        env.set_position_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name, FuturePosition)
        env.set_position_model(DEFAULT_ACCOUNT_TYPE.BENCHMARK.name, StockPosition)

        # 注入 API
        if DEFAULT_ACCOUNT_TYPE.FUTURE.name in env.config.base.accounts:
            # 注入期货API
            for export_name in api_future.__all__:
                export_as_api(getattr(api_future, export_name))
        if DEFAULT_ACCOUNT_TYPE.STOCK.name in env.config.base.accounts:
            # 注入股票API
            for export_name in api_stock.__all__:
                export_as_api(getattr(api_stock, export_name))

    def tear_down(self, code, exception=None):
        pass
