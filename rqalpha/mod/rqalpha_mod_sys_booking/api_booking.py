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

from rqalpha.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.const import EXECUTION_PHASE, POSITION_DIRECTION
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha import export_as_api

from . import mod_name


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_positions(booking=None):
    env = Environment.get_instance()
    mod = env.mod_dict[mod_name]
    booking_account = mod.booking_account
    return booking_account.get_positions(booking)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('direction').is_in([POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT]))
def get_position(order_book_id, direction, booking=None):
    env = Environment.get_instance()
    mod = env.mod_dict[mod_name]
    booking_account = mod.booking_account
    return booking_account.get_position(order_book_id, direction, booking)