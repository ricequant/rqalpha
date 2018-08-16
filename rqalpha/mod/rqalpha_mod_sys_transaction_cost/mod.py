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
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, MARKET

from .deciders import CNStockTransactionCostDecider, CNFutureTransactionCostDecider, HKStockTransactionCostDecider


class TransactionCostMod(AbstractMod):
    def start_up(self, env, mod_config):
        env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.STOCK, MARKET.CN, CNStockTransactionCostDecider(
            mod_config.commission_multiplier, mod_config.cn_stock_min_commission
        ))

        env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.FUTURE, MARKET.CN, CNFutureTransactionCostDecider(
            mod_config.commission_multiplier
        ))

        env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.STOCK, MARKET.HK, HKStockTransactionCostDecider(
            mod_config.commission_multiplier, mod_config.hk_stock_min_commission
        ))

    def tear_down(self, code, exception=None):
        pass
