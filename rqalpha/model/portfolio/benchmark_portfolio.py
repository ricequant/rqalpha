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

from .stock_portfolio import StockPortfolio
from ...const import ACCOUNT_TYPE


class BenchmarkPortfolio(StockPortfolio):
    def __init__(self, starting_cash, start_date):
        super(BenchmarkPortfolio, self).__init__(starting_cash, start_date)
        self._account_type = ACCOUNT_TYPE.BENCHMARK
