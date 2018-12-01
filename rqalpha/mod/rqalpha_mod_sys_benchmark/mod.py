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
from rqalpha.utils.logger import system_log
from rqalpha.const import RUN_TYPE

from .benchmark_portfolio import BackTestPriceSeriesBenchmarkPortfolio, RealTimePriceSeriesBenchmarkPortfolio


class BenchmarkMod(AbstractMod):
    def start_up(self, env, mod_config):

        # forward compatible
        try:
            order_book_id = mod_config.order_book_id or env.config.base.benchmark
        except AttributeError:
            order_book_id = None

        if not order_book_id:
            system_log.info("No order_book_id set, BenchmarkMod disabled.")
            return

        benchmark_portfolio = BackTestPriceSeriesBenchmarkPortfolio(
            order_book_id
        ) if env.config.base.run_type == RUN_TYPE.BACKTEST else RealTimePriceSeriesBenchmarkPortfolio(
            order_book_id
        )
        env.set_benchmark_portfolio(benchmark_portfolio)

    def tear_down(self, code, exception=None):
        pass
