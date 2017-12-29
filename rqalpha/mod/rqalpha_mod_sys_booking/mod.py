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


class BookingMod(AbstractMod):

    def start_up(self, env, mod_config):
        pass

    def tear_down(self, code, exception=None):
        pass
