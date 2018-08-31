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
from rqalpha.utils.exception import patch_user_exc

from .deciders import CNStockTransactionCostDecider, CNFutureTransactionCostDecider, HKStockTransactionCostDecider


class TransactionCostMod(AbstractMod):
    def start_up(self, env, mod_config):
        if mod_config.commission_multiplier < 0:
            raise patch_user_exc(ValueError(_(u"invalid commission multiplier value: value range is [0, +∞)")))

        if env.config.base.market == MARKET.CN:
            env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.STOCK, CNStockTransactionCostDecider(
                mod_config.commission_multiplier, mod_config.cn_stock_min_commission
            ))

            env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.FUTURE, CNFutureTransactionCostDecider(
                mod_config.commission_multiplier
            ))

        elif env.config.base.market == MARKET.HK:
            env.set_transaction_cost_decider(DEFAULT_ACCOUNT_TYPE.STOCK, HKStockTransactionCostDecider(
                mod_config.commission_multiplier, mod_config.hk_stock_min_commission
            ))

    def tear_down(self, code, exception=None):
        pass
