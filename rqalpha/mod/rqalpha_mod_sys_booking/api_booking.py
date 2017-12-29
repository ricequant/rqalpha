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

from __future__ import division
import six
import numpy as np

from rqalpha.api.api_base import decorate_api_exc, instruments, cal_style
from rqalpha.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.model.order import Order, MarketOrder, LimitOrder, OrderStyle
from rqalpha.const import EXECUTION_PHASE, SIDE, POSITION_EFFECT, ORDER_TYPE, RUN_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils import is_valid_price
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.arg_checker import apply_rules, verify_that


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('booking').is_instance_of(str))
def get_positions(booking=None):
    raise NotImplementedError