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

import copy
import datetime
from typing import Dict, Callable, Optional

import numpy as np

from rqalpha.environment import Environment
from rqalpha.const import INSTRUMENT_TYPE, POSITION_DIRECTION, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils import TimeRange, INST_TYPE_IN_STOCK_ACCOUNT
from rqalpha.utils.repr import property_repr, PropertyReprMeta


class Instrument(metaclass=PropertyReprMeta):
    DEFAULT_LISTED_DATE = datetime.datetime(1990, 1, 1)
    DEFAULT_DE_LISTED_DATE = datetime.datetime(2999, 12, 31)

    @staticmethod
    def _fix_date(ds, dflt):
        if isinstance(ds, datetime.datetime):
            return ds
        if ds == '0000-00-00':
            return dflt
        year, month, day = ds.split('-')
        return datetime.datetime(int(year), int(month), int(day))

    __repr__ = property_repr

    def __init__(self, dic, future_tick_size_getter=None):
        # type: (Dict, Optional[Callable[[Instrument], float]]) -> None
        self.__dict__ = copy.copy(dic)
        self._future_tick_size_getter = future_tick_size_getter

        if "listed_date" in dic:
            self.__dict__["listed_date"] = self._fix_date(dic["listed_date"], self.DEFAULT_LISTED_DATE)
        if "de_listed_date" in dic:
            self.__dict__["de_listed_date"] = self._fix_date(dic["de_listed_date"], self.DEFAULT_DE_LISTED_DATE)
        if "maturity_date" in self.__dict__:
            self.__dict__["maturity_date"] = self._fix_date(dic["maturity_date"], self.DEFAULT_DE_LISTED_DATE)

        if 'contract_multiplier' in dic:
            if np.isnan(self.contract_multiplier):
                raise RuntimeError("Contract multiplier of {} is not supposed to be nan".format(self.order_book_id))

    @property
    def order_book_id(self):
        # type: () -> str
        """
        [str] 股票：证券代码，证券的独特的标识符。应以’.XSHG’或’.XSHE’结尾，前者代表上证，后者代表深证。
        期货：期货代码，期货的独特的标识符（郑商所期货合约数字部分进行了补齐。例如原有代码’ZC609’补齐之后变为’ZC1609’）。
        主力连续合约UnderlyingSymbol+88，例如’IF88’ ；指数连续合约命名规则为UnderlyingSymbol+99
        """
        return self.__dict__["order_book_id"]

    @property
    def symbol(self):
        # type: () -> str
        """
        [str] 股票：证券的简称，例如’平安银行’。期货：期货的简称，例如’沪深1005’。
        """
        return self.__dict__["symbol"]

    @property
    def round_lot(self):
        # type: () -> int
        """
        [int] 股票：一手对应多少股，中国A股一手是100股。期货：一律为1。
        """
        return self.__dict__["round_lot"]

    @property
    def listed_date(self):
        # type: () -> datetime.datetime
        """
        [datetime] 股票：该证券上市日期。期货：期货的上市日期，主力连续合约与指数连续合约都为 datetime(1990, 1, 1)。
        """
        return self.__dict__["listed_date"]

    @property
    def de_listed_date(self):
        # type: () -> datetime.datetime
        """
        [datetime] 股票：退市日期。期货：交割日期。
        """
        return self.__dict__["de_listed_date"]

    @property
    def type(self):
        # type: () -> str
        """
        [sty] 合约类型，目前支持的类型有: ‘CS’, ‘INDX’, ‘LOF’, ‘ETF’, ‘Future’
        """
        return INSTRUMENT_TYPE[self.__dict__["type"]]

    @property
    def exchange(self):
        # type: () -> str
        """
        [str] 交易所。股票：’XSHE’ - 深交所, ‘XSHG’ - 上交所。期货：’DCE’ - 大连商品交易所, ‘SHFE’ - 上海期货交易所，
        ’CFFEX’ - 中国金融期货交易所, ‘CZCE’- 郑州商品交易所
        """
        return self.__dict__["exchange"]

    @property
    def market_tplus(self):
        # type: () -> int
        """
        [int] 合约卖出和买入操作需要间隔的最小交易日数，如A股为 1
        公募基金的 market_tplus 默认0
        """
        return self.__dict__.get("market_tplus") or 0

    @property
    def sector_code(self):
        """
        [str] 板块缩写代码，全球通用标准定义（股票专用）
        """
        try:
            return self.__dict__["sector_code"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'sector_code' ".format(self.order_book_id)
            )

    @property
    def sector_code_name(self):
        """
        [str] 以当地语言为标准的板块代码名（股票专用）
        """
        try:
            return self.__dict__["sector_code_name"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'sector_code_name' ".format(self.order_book_id)
            )

    @property
    def industry_code(self):
        """
        [str] 国民经济行业分类代码，具体可参考“Industry列表” （股票专用）
        """
        try:
            return self.__dict__["industry_code"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'industry_code' ".format(self.order_book_id)
            )

    @property
    def industry_name(self):
        """
        [str] 国民经济行业分类名称（股票专用）
        """
        try:
            return self.__dict__["industry_name"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'industry_name' ".format(self.order_book_id)
            )

    @property
    def concept_names(self):
        """
        [str] 概念股分类，例如：’铁路基建’，’基金重仓’等（股票专用）
        """
        try:
            return self.__dict__["concept_names"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'concept_names' ".format(self.order_book_id)
            )

    @property
    def board_type(self):
        """
        [str] 板块类别，’MainBoard’ - 主板,’GEM’ - 创业板（股票专用）
        """
        try:
            return self.__dict__["board_type"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'board_type' ".format(self.order_book_id)
            )

    @property
    def status(self):
        """
        [str] 合约状态。’Active’ - 正常上市, ‘Delisted’ - 终止上市, ‘TemporarySuspended’ - 暂停上市,
        ‘PreIPO’ - 发行配售期间, ‘FailIPO’ - 发行失败（股票专用）
        """
        try:
            return self.__dict__["status"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'status' ".format(self.order_book_id)
            )

    @property
    def special_type(self):
        """
        [str] 特别处理状态。’Normal’ - 正常上市, ‘ST’ - ST处理, ‘StarST’ - *ST代表该股票正在接受退市警告,
        ‘PT’ - 代表该股票连续3年收入为负，将被暂停交易, ‘Other’ - 其他（股票专用）
        """
        try:
            return self.__dict__["special_type"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'special_type' ".format(self.order_book_id)
            )

    @property
    def contract_multiplier(self):
        """
        [float] 合约乘数，例如沪深300股指期货的乘数为300.0（期货专用）
        """
        return self.__dict__.get('contract_multiplier', 1)

    @property
    def margin_rate(self):
        """
        [float] 合约最低保证金率（期货专用）
        """
        return self.__dict__.get("margin_rate", 1)

    @property
    def underlying_order_book_id(self):
        """
        [str] 合约标的代码，目前除股指期货(IH, IF, IC)之外的期货合约，这一字段全部为’null’（期货专用）
        """
        try:
            return self.__dict__["underlying_order_book_id"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'underlying_order_book_id' ".format(self.order_book_id)
            )

    @property
    def underlying_symbol(self):
        """
        [str] 合约标的代码，目前除股指期货(IH, IF, IC)之外的期货合约，这一字段全部为’null’（期货专用）
        """
        try:
            return self.__dict__["underlying_symbol"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'underlying_symbol' ".format(self.order_book_id)
            )

    @property
    def maturity_date(self):
        # type: () -> datetime.datetime
        """
        [datetime] 到期日
        """
        try:
            return self.__dict__["maturity_date"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'maturity_date' ".format(self.order_book_id)
            )

    @property
    def settlement_method(self):
        """
        [str] 交割方式，’CashSettlementRequired’ - 现金交割, ‘PhysicalSettlementRequired’ - 实物交割（期货专用）
        """
        try:
            return self.__dict__["settlement_method"]
        except (KeyError, ValueError):
            raise AttributeError(
                "Instrument(order_book_id={}) has no attribute 'settlement_method' ".format(self.order_book_id)
            )

    @property
    def listing(self):
        """
        [bool] 该合约当前日期是否在交易
        """
        trading_dt = Environment.get_instance().trading_dt
        return self.listing_at(trading_dt)

    @property
    def listed(self):
        """
        [bool] 该合约当前交易日是否已上市
        """
        return self.listed_at(Environment.get_instance().trading_dt)

    @property
    def de_listed(self):
        """
        [bool] 该合约当前交易日是否已退市
        """
        return self.de_listed_at(Environment.get_instance().trading_dt)

    @property
    def account_type(self):
        if self.type in INST_TYPE_IN_STOCK_ACCOUNT:
            return DEFAULT_ACCOUNT_TYPE.STOCK
        elif self.type == INSTRUMENT_TYPE.FUTURE:
            return DEFAULT_ACCOUNT_TYPE.FUTURE
        else:
            raise NotImplementedError

    def listing_at(self, dt):
        """
        该合约在指定日期是否在交易
        :param dt: datetime.datetime
        :return: bool
        """
        return self.listed_at(dt) and not self.de_listed_at(dt)

    def listed_at(self, dt):
        """
        该合约在指定日期是否已上日
        :param dt: datetime.datetime
        :return: bool
        """
        return self.listed_date <= dt

    def de_listed_at(self, dt):
        """
        该合约在指定日期是否已退市
        :param dt: datetime.datetime
        :return: bool
        """
        if self.type in (INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.OPTION):
            return dt.date() > self.de_listed_date.date()
        else:
            return dt >= self.de_listed_date

    STOCK_TRADING_PERIOD = [
        TimeRange(start=datetime.time(9, 31), end=datetime.time(11, 30)),
        TimeRange(start=datetime.time(13, 1), end=datetime.time(15, 0)),
    ]

    @property
    def trading_hours(self):
        # trading_hours='09:31-11:30,13:01-15:00'
        try:
            trading_hours = self.__dict__["trading_hours"]
        except KeyError:
            if self.type in INST_TYPE_IN_STOCK_ACCOUNT:
                return self.STOCK_TRADING_PERIOD
            return None
        trading_period = []
        trading_hours = trading_hours.replace("-", ":")
        for time_range_str in trading_hours.split(","):
            start_h, start_m, end_h, end_m = (int(i) for i in time_range_str.split(":"))
            start, end = datetime.time(start_h, start_m), datetime.time(end_h, end_m)
            if start > end:
                trading_period.append(TimeRange(start, datetime.time(23, 59)))
                trading_period.append(TimeRange(datetime.time(0, 0), end))
            else:
                trading_period.append(TimeRange(start, end))
        return trading_period

    @property
    def trade_at_night(self):
        return any(r.start <= datetime.time(4, 0) or r.end >= datetime.time(19, 0) for r in (self.trading_hours or []))

    def days_from_listed(self):
        if self.listed_date == self.DEFAULT_LISTED_DATE:
            return -1

        date = Environment.get_instance().trading_dt.date()
        if self.de_listed_date.date() < date:
            return -1

        ipo_days = (date - self.listed_date.date()).days
        return ipo_days if ipo_days >= 0 else -1

    def days_to_expire(self):
        if self.type != 'Future' or self.order_book_id[-2:] == '88' or self.order_book_id[-2:] == '99':
            return -1

        date = Environment.get_instance().trading_dt.date()
        days = (self.maturity_date.date() - date).days
        return -1 if days < 0 else days

    def tick_size(self):
        # type: () -> float
        if self.type in (INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.INDX):
            return 0.01
        elif self.type in ("ETF", "LOF"):
            return 0.001
        elif self.type == INSTRUMENT_TYPE.FUTURE:
            return self._future_tick_size_getter(self)
        else:
            raise NotImplementedError

    def calc_cash_occupation(self, price, quantity, direction):
        # type: (float, float, POSITION_DIRECTION) -> float
        if self.type in INST_TYPE_IN_STOCK_ACCOUNT:
            return price * quantity
        elif self.type == INSTRUMENT_TYPE.FUTURE:
            margin_multiplier = Environment.get_instance().config.base.margin_multiplier
            return price * quantity * self.contract_multiplier * self.margin_rate * margin_multiplier
        else:
            raise NotImplementedError


class SectorCodeItem(object):
    def __init__(self, cn, en, name):
        self.__cn = cn
        self.__en = en
        self.__name = name

    @property
    def cn(self):
        return self.__cn

    @property
    def en(self):
        return self.__en

    @property
    def name(self):
        return self.__name

    def __repr__(self):
        return "{}: {}, {}".format(self.__name, self.__en, self.__cn)


class SectorCode(object):
    Energy = SectorCodeItem("能源", "energy", 'Energy')
    Materials = SectorCodeItem("原材料", "materials", 'Materials')
    ConsumerDiscretionary = SectorCodeItem("非必需消费品", "consumer discretionary", 'ConsumerDiscretionary')
    ConsumerStaples = SectorCodeItem("必需消费品", "consumer staples", 'ConsumerStaples')
    HealthCare = SectorCodeItem("医疗保健", "health care", 'HealthCare')
    Financials = SectorCodeItem("金融", "financials", 'Financials')
    InformationTechnology = SectorCodeItem("信息技术", "information technology", 'InformationTechnology')
    TelecommunicationServices = SectorCodeItem("电信服务", "telecommunication services", 'TelecommunicationServices')
    Utilities = SectorCodeItem("公共服务", "utilities", 'Utilities')
    Industrials = SectorCodeItem("工业", "industrials", "Industrials")


class IndustryCodeItem(object):
    def __init__(self, code, name):
        self.__code = code
        self.__name = name

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    def __repr__(self):
        return "{0}:{1}".format(self.__code, self.__name)


class IndustryCode(object):
    A01 = IndustryCodeItem("A01", "农业")
    A02 = IndustryCodeItem("A02", "林业")
    A03 = IndustryCodeItem("A03", "畜牧业")
    A04 = IndustryCodeItem("A04", "渔业")
    A05 = IndustryCodeItem("A05", "农、林、牧、渔服务业")
    B06 = IndustryCodeItem("B06", "煤炭开采和洗选业")
    B07 = IndustryCodeItem("B07", "石油和天然气开采业")
    B08 = IndustryCodeItem("B08", "黑色金属矿采选业")
    B09 = IndustryCodeItem("B09", "有色金属矿采选业")
    B10 = IndustryCodeItem("B10", "非金属矿采选业")
    B11 = IndustryCodeItem("B11", "开采辅助活动")
    B12 = IndustryCodeItem("B12", "其他采矿业")
    C13 = IndustryCodeItem("C13", "农副食品加工业")
    C14 = IndustryCodeItem("C14", "食品制造业")
    C15 = IndustryCodeItem("C15", "酒、饮料和精制茶制造业")
    C16 = IndustryCodeItem("C16", "烟草制品业")
    C17 = IndustryCodeItem("C17", "纺织业")
    C18 = IndustryCodeItem("C18", "纺织服装、服饰业")
    C19 = IndustryCodeItem("C19", "皮革、毛皮、羽毛及其制品和制鞋业")
    C20 = IndustryCodeItem("C20", "木材加工及木、竹、藤、棕、草制品业")
    C21 = IndustryCodeItem("C21", "家具制造业")
    C22 = IndustryCodeItem("C22", "造纸及纸制品业")
    C23 = IndustryCodeItem("C23", "印刷和记录媒介复制业")
    C24 = IndustryCodeItem("C24", "文教、工美、体育和娱乐用品制造业")
    C25 = IndustryCodeItem("C25", "石油加工、炼焦及核燃料加工业")
    C26 = IndustryCodeItem("C26", "化学原料及化学制品制造业")
    C27 = IndustryCodeItem("C27", "医药制造业")
    C28 = IndustryCodeItem("C28", "化学纤维制造业")
    C29 = IndustryCodeItem("C29", "橡胶和塑料制品业")
    C30 = IndustryCodeItem("C30", "非金属矿物制品业")
    C31 = IndustryCodeItem("C31", "黑色金属冶炼及压延加工业")
    C32 = IndustryCodeItem("C32", "有色金属冶炼和压延加工业")
    C33 = IndustryCodeItem("C33", "金属制品业")
    C34 = IndustryCodeItem("C34", "通用设备制造业")
    C35 = IndustryCodeItem("C35", "专用设备制造业")
    C36 = IndustryCodeItem("C36", "汽车制造业")
    C37 = IndustryCodeItem("C37", "铁路、船舶、航空航天和其它运输设备制造业")
    C38 = IndustryCodeItem("C38", "电气机械及器材制造业")
    C39 = IndustryCodeItem("C39", "计算机、通信和其他电子设备制造业")
    C40 = IndustryCodeItem("C40", "仪器仪表制造业")
    C41 = IndustryCodeItem("C41", "其他制造业")
    C42 = IndustryCodeItem("C42", "废弃资源综合利用业")
    C43 = IndustryCodeItem("C43", "金属制品、机械和设备修理业")
    D44 = IndustryCodeItem("D44", "电力、热力生产和供应业")
    D45 = IndustryCodeItem("D45", "燃气生产和供应业")
    D46 = IndustryCodeItem("D46", "水的生产和供应业")
    E47 = IndustryCodeItem("E47", "房屋建筑业")
    E48 = IndustryCodeItem("E48", "土木工程建筑业")
    E49 = IndustryCodeItem("E49", "建筑安装业")
    E50 = IndustryCodeItem("E50", "建筑装饰和其他建筑业")
    F51 = IndustryCodeItem("F51", "批发业")
    F52 = IndustryCodeItem("F52", "零售业")
    G53 = IndustryCodeItem("G53", "铁路运输业")
    G54 = IndustryCodeItem("G54", "道路运输业")
    G55 = IndustryCodeItem("G55", "水上运输业")
    G56 = IndustryCodeItem("G56", "航空运输业")
    G57 = IndustryCodeItem("G57", "管道运输业")
    G58 = IndustryCodeItem("G58", "装卸搬运和运输代理业")
    G59 = IndustryCodeItem("G59", "仓储业")
    G60 = IndustryCodeItem("G60", "邮政业")
    H61 = IndustryCodeItem("H61", "住宿业")
    H62 = IndustryCodeItem("H62", "餐饮业")
    I63 = IndustryCodeItem("I63", "电信、广播电视和卫星传输服务")
    I64 = IndustryCodeItem("I64", "互联网和相关服务")
    I65 = IndustryCodeItem("I65", "软件和信息技术服务业")
    J66 = IndustryCodeItem("J66", "货币金融服务")
    J67 = IndustryCodeItem("J67", "资本市场服务")
    J68 = IndustryCodeItem("J68", "保险业")
    J69 = IndustryCodeItem("J69", "其他金融业")
    K70 = IndustryCodeItem("K70", "房地产业")
    L71 = IndustryCodeItem("L71", "租赁业")
    L72 = IndustryCodeItem("L72", "商务服务业")
    M73 = IndustryCodeItem("M73", "研究和试验发展")
    M74 = IndustryCodeItem("M74", "专业技术服务业")
    M75 = IndustryCodeItem("M75", "科技推广和应用服务业")
    N76 = IndustryCodeItem("N76", "水利管理业")
    N77 = IndustryCodeItem("N77", "生态保护和环境治理业")
    N78 = IndustryCodeItem("N78", "公共设施管理业")
    O79 = IndustryCodeItem("O79", "居民服务业")
    O80 = IndustryCodeItem("O80", "机动车、电子产品和日用产品修理业")
    O81 = IndustryCodeItem("O81", "其他服务业")
    P82 = IndustryCodeItem("P82", "教育")
    Q83 = IndustryCodeItem("Q83", "卫生")
    Q84 = IndustryCodeItem("Q84", "社会工作")
    R85 = IndustryCodeItem("R85", "新闻和出版业")
    R86 = IndustryCodeItem("R86", "广播、电视、电影和影视录音制作业")
    R87 = IndustryCodeItem("R87", "文化艺术业")
    R88 = IndustryCodeItem("R88", "体育")
    R89 = IndustryCodeItem("R89", "娱乐业")
    S90 = IndustryCodeItem("S90", "综合")
