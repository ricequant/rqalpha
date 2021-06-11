# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

from enum import Enum, EnumMeta


class CustomEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        enum_class = super(CustomEnumMeta, metacls).__new__(metacls, cls, bases, classdict)
        enum_class._member_reverse_map = {v.value: v for v in enum_class.__members__.values()}
        return enum_class

    def __contains__(cls, member):
        if super(CustomEnumMeta, cls).__contains__(member):
            return True
        if isinstance(member, str):
            return member in cls._member_reverse_map
        return False

    def __getitem__(self, item):
        try:
            return super(CustomEnumMeta, self).__getitem__(item)
        except KeyError:
            return self._member_reverse_map[item]


class CustomEnum(str, Enum, metaclass=CustomEnumMeta):
    def __repr__(self):
        return "%s.%s" % (
            self.__class__.__name__, self._name_)


# noinspection PyPep8Naming
class EXECUTION_PHASE(CustomEnum):
    GLOBAL = "[全局]"
    ON_INIT = "[程序初始化]"
    BEFORE_TRADING = "[日内交易前]"
    OPEN_AUCTION = "[集合竞价]"
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
    *   关于 ACCOUNT_TYPE，目前主要表示为交易账户。STOCK / FUTURE / BOND 目前均表示为中国 对应的交易账户。
    *   ACCOUNT_TYPE 不区分交易所，比如 A 股区分上海交易所和深圳交易所，但对应的都是一个账户，因此统一为 STOCK
    *   目前暂时不添加其他 DEFAULT_ACCOUNT_TYPE 类型，如果需要增加自定义账户及类型，请参考 https://github.com/ricequant/rqalpha/issues/160
    """
    # 股票
    STOCK = "STOCK"
    # 期货
    FUTURE = "FUTURE"
    # 债券
    BOND = "BOND"


# noinspection PyPep8Naming
class MATCHING_TYPE(CustomEnum):
    CURRENT_BAR_CLOSE = "CURRENT_BAR_CLOSE"
    VWAP = "VWAP"
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
    PENDING_NEW = "PENDING_NEW"        # 待报
    ACTIVE = "ACTIVE"                  # 已报/部成
    FILLED = "FILLED"                  # 已成
    REJECTED = "REJECTED"              # 拒单
    PENDING_CANCEL = "PENDING_CANCEL"  # 待撤
    CANCELLED = "CANCELLED"            # 已撤


# noinspection PyPep8Naming
class SIDE(CustomEnum):
    BUY = "BUY"                      # 买
    SELL = "SELL"                    # 卖
    FINANCING = "FINANCING"          # 正回购
    MARGIN = "MARGIN"                # 逆回购
    CONVERT_STOCK = "CONVERT_STOCK"  # 转股


# noinspection PyPep8Naming
class POSITION_EFFECT(CustomEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    CLOSE_TODAY = "CLOSE_TODAY"
    EXERCISE = "EXERCISE"
    MATCH = "MATCH"


# noinspection PyPep8Naming
class POSITION_DIRECTION(CustomEnum):
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
    FUTURE = "Future"
    OPTION = "Option"
    ETF = "ETF"
    LOF = "LOF"
    INDX = "INDX"
    PUBLIC_FUND = 'PublicFund'
    BOND = "Bond"
    CONVERTIBLE = "Convertible"
    SPOT = "Spot"
    REPO = "Repo"


# noinspection PyPep8Naming
class PERSIST_MODE(CustomEnum):
    ON_CRASH = "ON_CRASH"
    REAL_TIME = "REAL_TIME"
    ON_NORMAL_EXIT = "ON_NORMAL_EXIT"


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


# noinspection PyPep8Naming
class MARKET(CustomEnum):
    CN = "CN"
    HK = "HK"


# noinspection PyPep8Naming
class TRADING_CALENDAR_TYPE(CustomEnum):
    EXCHANGE = "EXCHANGE"
    INTER_BANK = "INTERBANK"


UNDERLYING_SYMBOL_PATTERN = "([a-zA-Z]+)\d+"
