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


# noinspection PyPep8Naming
class EXECUTION_PHASE(CustomEnum):
    GLOBAL = "[全局]"
    ON_INIT = "[程序初始化]"
    BEFORE_TRADING = "[日内交易前]"
    ON_BAR = "[盘中 handle_bar 函数]"
    ON_TICK = "[盘中 handle_tick 函数]"
    AFTER_TRADING = "[日内交易后]"
    FINALIZED = "[程序结束]"
    SCHEDULED = "[scheduler函数内]"


# noinspection PyPep8Naming
class RUN_TYPE(CustomEnum):
    # TODO: 取消 RUN_TYPE, 取而代之的是使用开启哪些Mod来控制策略所运行的类型
    # Back Test
    BACKTEST = "BACKTEST"
    # Paper Trading
    PAPER_TRADING = "PAPER_TRADING"
    # Live Trading
    LIVE_TRADING = 'LIVE_TRADING'


# noinspection PyPep8Naming
class DEFAULT_ACCOUNT_TYPE(CustomEnum):
    """
    *   关于 ACCOUNT_TYPE，目前主要表示为交易账户。STOCK / FUTURE / OPTION 目前均表示为中国 对应的交易账户。
    *   ACCOUNT_TYPE 不区分交易所，比如 A 股区分上海交易所和深圳交易所，但对应的都是一个账户，因此统一为 STOCK
    *   目前暂时不添加其他 DEFAULT_ACCOUNT_TYPE 类型，如果需要增加自定义账户及类型，请参考 https://github.com/ricequant/rqalpha/issues/160
    """
    TOTAL = 0
    BENCHMARK = 1
    # 股票
    STOCK = 2
    # 期货
    FUTURE = 3
    # 期权
    OPTION = 4


# noinspection PyPep8Naming
class BAR_STATUS(CustomEnum):
    LIMIT_UP = "LIMIT_UP"
    LIMIT_DOWN = "LIMIT_DOWN"
    NORMAL = "NORMAL"
    ERROR = "ERROR"


# noinspection PyPep8Naming
class MATCHING_TYPE(CustomEnum):
    CURRENT_BAR_CLOSE = "CURRENT_BAR_CLOSE"
    NEXT_BAR_OPEN = "NEXT_BAR_OPEN"
    NEXT_TICK_LAST = "NEXT_TICK_LAST"
    NEXT_TICK_BEST_OWN = "NEXT_TICK_BEST_OWN"
    NEXT_TICK_BEST_COUNTERPARTY = "NEXT_TICK_BEST_COUNTERPARTY"


# noinspection PyPep8Naming
class ORDER_TYPE(CustomEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


# noinspection PyPep8Naming
class ORDER_STATUS(CustomEnum):
    PENDING_NEW = "PENDING_NEW"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELLED = "CANCELLED"


# noinspection PyPep8Naming
class SIDE(CustomEnum):
    BUY = "BUY"
    SELL = "SELL"


# noinspection PyPep8Naming
class POSITION_EFFECT(CustomEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    CLOSE_TODAY = "CLOSE_TODAY"


# noinspection PyPep8Naming
class POSITION_DIRECTION(CustomEnum):
    UNKNOWN = "UNKNOWN"
    LONG = "LONG"
    SHORT = "SHORT"


# noinspection PyPep8Naming
class EXC_TYPE(CustomEnum):
    USER_EXC = "USER_EXC"
    SYSTEM_EXC = "SYSTEM_EXC"
    NOTSET = "NOTSET"


# noinspection PyPep8Naming
class INSTRUMENT_TYPE(CustomEnum):
    CS = "CS"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    ETF = "ETF"
    LOF = "LOF"
    INDX = "INDX"
    FENJI_MU = "FENJI_MU"
    FENJI_A = "FENJI_A"
    FENJI_B = "FENJI_B"
    PUBLIC_FUND = 'PublicFund'


# noinspection PyPep8Naming
class PERSIST_MODE(CustomEnum):
    ON_CRASH = "ON_CRASH"
    REAL_TIME = "REAL_TIME"
    ON_NORMAL_EXIT = "ON_NORMAL_EXIT"


# noinspection PyPep8Naming
class MARGIN_TYPE(CustomEnum):
    BY_MONEY = "BY_MONEY"
    BY_VOLUME = "BY_VOLUME"


# noinspection PyPep8Naming
class COMMISSION_TYPE(CustomEnum):
    BY_MONEY = "BY_MONEY"
    BY_VOLUME = "BY_VOLUME"


# noinspection PyPep8Naming
class EXIT_CODE(CustomEnum):
    EXIT_SUCCESS = "EXIT_SUCCESS"
    EXIT_USER_ERROR = "EXIT_USER_ERROR"
    EXIT_INTERNAL_ERROR = "EXIT_INTERNAL_ERROR"


# noinspection PyPep8Naming
class HEDGE_TYPE(CustomEnum):
    HEDGE = "hedge"
    SPECULATION = "speculation"
    ARBITRAGE = "arbitrage"


# noinspection PyPep8Naming
class DAYS_CNT(object):
    DAYS_A_YEAR = 365
    TRADING_DAYS_A_YEAR = 252


class CURRENCY(CustomEnum):
    CNY = "CNY"     # 人民币
    USD = "USD"     # 美元
    EUR = "EUR"     # 欧元
    HKD = "HKD"     # 港币
    GBP = "GBP"     # 英镑
    JPY = "JPY"     # 日元
    KRW = "KWR"     # 韩元
    CAD = "CAD"     # 加元
    AUD = "AUD"     # 澳元
    CHF = "CHF"     # 瑞郎
    SGD = "SGD"     # 新加坡元
    MYR = "MYR"     # 马拉西亚币
    IDR = "IDR"     # 印尼币
    NZD = "NZD"     # 新西兰币
    VND = "VND"     # 越南盾
    THB = "THB"     # 泰铢
    PHP = "PHP"     # 菲律宾币


UNDERLYING_SYMBOL_PATTERN = "([a-zA-Z]+)\d+"

NIGHT_TRADING_NS = ["CU", "AL", "ZN", "PB", "SN", "NI", "RB", "HC", "BU", "RU", "AU", "AG", "Y", "M", "A", "B", "P",
                    "J", "JM", "I", "CF", "SR", "OI", "MA", "ZC", "FG", "RM", "CY", "TA", "SC"]
