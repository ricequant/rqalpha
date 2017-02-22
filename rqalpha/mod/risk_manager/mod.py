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
from rqalpha.events import EVENT
from rqalpha.utils import get_account_type
from rqalpha.const import ACCOUNT_TYPE

from .frontend_validator import StockFrontendValidator, FutureFrontendValidator


class RiskManagerMod(AbstractMod):

    def __init__(self):
        self._env = None
        self.mod_config = None
        self._frontend_validator = {}

    def start_up(self, env, mod_config):
        self._env = env
        self.mod_config = mod_config
        self._env.event_bus.prepend_listener(EVENT.ORDER_PENDING_NEW, self._frontend_validate)

    def tear_down(self, code, exception=None):
        pass

    def _frontend_validate(self, account, order):
        frontend_validator = self._get_frontend_validator_for(order.order_book_id)
        frontend_validator.order_pipeline(account, order)

    def _get_frontend_validator_for(self, order_book_id):
        account_type = get_account_type(order_book_id)
        try:
            return self._frontend_validator[account_type]
        except KeyError:
            if account_type == ACCOUNT_TYPE.STOCK:
                validator = StockFrontendValidator(self.mod_config)
            elif account_type == ACCOUNT_TYPE.FUTURE:
                validator = FutureFrontendValidator(self.mod_config)
            else:
                raise RuntimeError('account type {} not supported yet'.format(account_type))
            self._frontend_validator[account_type] = validator
            return validator

