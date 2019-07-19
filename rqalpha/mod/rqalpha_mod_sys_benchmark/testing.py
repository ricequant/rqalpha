# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from rqalpha.utils.testing import DataProxyFixture
from rqalpha.mod.rqalpha_mod_sys_benchmark.benchmark_provider import BackTestPriceSeriesBenchmarkProvider


class PriceSeriesBenchmarkProviderFixture(DataProxyFixture):
    def __init__(self, *args, **kwargs):
        super(PriceSeriesBenchmarkProviderFixture, self).__init__(*args, **kwargs)

        self.benchmark_provider = None
        self.benchmark_order_book_id = None
        self.provider_class = BackTestPriceSeriesBenchmarkProvider

    def init_fixture(self):
        super(PriceSeriesBenchmarkProviderFixture, self).init_fixture()
        self.benchmark_provider = self.provider_class (self.benchmark_order_book_id)
