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
from rqalpha.const import ACCOUNT_TYPE

from .account_model import *
from .position_model import *


class AccountMod(AbstractMod):

    def start_up(self, env, mod_config):
        env.set_account_model(ACCOUNT_TYPE.STOCK, StockAccount)
        env.set_account_model(ACCOUNT_TYPE.FUTURE, FutureAccount)
        env.set_account_model(ACCOUNT_TYPE.BENCHMARK, BenchmarkAccount)

        env.set_position_model(ACCOUNT_TYPE.STOCK, StockPosition)
        env.set_position_model(ACCOUNT_TYPE.FUTURE, FuturePosition)
        env.set_position_model(ACCOUNT_TYPE.BENCHMARK, StockPosition)

    def tear_down(self, code, exception=None):
        pass
