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

from enum import Enum


class CustomEnum(Enum):
    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_)


class EXECUTION_PHASE(CustomEnum):
    GLOBAL = "[全局]"
    ON_INIT = "[程序初始化]"
    BEFORE_TRADING = "[日内交易前]"
    ON_BAR = "[盘中 handle_bar 函数]"
    ON_TICK = "[盘中 handle_tick 函数]"
    AFTER_TRADING = "[日内交易后]"
    FINALIZED = "[程序结束]"
    SCHEDULED = "[scheduler函数内]"

RUN_TYPE = CustomEnum("RUN_TYPE", [
    # Back Test
    "BACKTEST",
    # Paper Trading
    "PAPER_TRADING",
])

ACCOUNT_TYPE = CustomEnum("ACCOUNT_TYPE", [
    "TOTAL",
    "BENCHMARK",
    "STOCK",
    "FUTURE",
])

BAR_STATUS = CustomEnum("BAR_STATUS", [
    "LIMIT_UP",
    "LIMIT_DOWN",
    "NORMAL",
    "ERROR",
])

MATCHING_TYPE = CustomEnum("MATCHING_TYPE", [
    "CURRENT_BAR_CLOSE",
    "NEXT_BAR_OPEN",
])

ORDER_TYPE = CustomEnum("ORDER_TYPE", [
    "MARKET",
    "LIMIT",
])

ORDER_STATUS = CustomEnum("ORDER_STATUS", [
    "PENDING_NEW",
    "ACTIVE",
    "FILLED",
    "REJECTED",
    "PENDING_CANCEL",
    "CANCELLED",
])

SIDE = CustomEnum("SIDE", [
    "BUY",
    "SELL",
])

POSITION_EFFECT = CustomEnum("POSITION_EFFECT", [
    "OPEN",
    "CLOSE",
])

EXC_TYPE = CustomEnum("EXC_TYPE", [
    "USER_EXC",
    "SYSTEM_EXC",
    "NOTSET",
])

INSTRUMENT_TYPE = CustomEnum("INSTRUMENT_TYPE", [
    "CS",
    "FUTURE",
    "OPTION",
    "ETF",
    "LOF",
    "INDX",
    "FENJI_MU",
    "FENJI_A",
    "FENJI_B",
])

PERSIST_MODE = CustomEnum("PERSIST_MODE", [
    "ON_CRASH",
    "REAL_TIME"
])

MARGIN_TYPE = CustomEnum("MARGIN_TYPE", [
    "BY_MONEY",
    "BY_VOLUME",
])

COMMISSION_TYPE = CustomEnum("COMMISSION_TYPE", [
    "BY_MONEY",
    "BY_VOLUME",
])

EXIT_CODE = CustomEnum("EXIT_CODE", [
    "EXIT_SUCCESS",
    "EXIT_USER_ERROR",
    "EXIT_INTERNAL_ERROR",
])


class HEDGE_TYPE(CustomEnum):
    HEDGE = "hedge"
    SPECULATION = "speculation"
    ARBITRAGE = "arbitrage"


class DAYS_CNT(object):
    DAYS_A_YEAR = 365
    TRADING_DAYS_A_YEAR = 252


UNDERLYING_SYMBOL_PATTERN = "([a-zA-Z]+)\d+"

NIGHT_TRADING_NS = ["CU", "AL", "ZN", "PB", "SN", "NI", "RB", "HC", "BU", "RU", "AU", "AG", "Y", "M", "A", "B", "P",
                    "J", "JM", "I", "CF", "SR", "OI", "MA", "ZC", "FG", "RM"]
