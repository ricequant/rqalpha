# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


from enum import Enum


ORDER_STATUS = Enum("ORDER_STATUS", [
    "OPEN",
    "FILLED",
    "REJECTED",
    "CANCELLED",
])


EVENT_TYPE = Enum("EVENT_TYPE", [
    "DAY_START",
    "HANDLE_BAR",
    "DAY_END",
])


EXECUTION_PHASE = Enum("EXECUTION_PHASE", [
    "INIT",
    "HANDLE_BAR",
    "BEFORE_TRADING",
    "SCHEDULED",
    "FINALIZED",
])


class DAYS_CNT(object):
    DAYS_A_YEAR = 365
    TRADING_DAYS_A_YEAR = 252
