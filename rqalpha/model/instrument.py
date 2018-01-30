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

import six
import datetime

from rqalpha.environment import Environment
from rqalpha.utils import instrument_type_str2enum


class Instrument(object):
    DEFAULT_LISTED_DATE = datetime.datetime(1990, 1, 1)
    DEFAULT_DE_LISTED_DATE = datetime.datetime(2999, 12, 31)

    @staticmethod
    def _fix_date(ds, dflt):
        if ds == '0000-00-00':
            return dflt
        year, month, day = ds.split('-')
        return datetime.datetime(int(year), int(month), int(day))

    def __init__(self, dic):
        self.__dict__ = dic
        if 'listed_date' in self.__dict__:
            self.listed_date = self._fix_date(self.listed_date, self.DEFAULT_LISTED_DATE)
        if 'de_listed_date' in self.__dict__:
            self.de_listed_date = self._fix_date(self.de_listed_date, self.DEFAULT_DE_LISTED_DATE)
        if 'maturity_date' in self.__dict__:
            self.maturity_date = self._fix_date(self.maturity_date, self.DEFAULT_DE_LISTED_DATE)

    def __repr__(self):
        return "{}({})".format(type(self).__name__,
                               ", ".join(["{}={}".format(k, repr(v))
                                          for k, v in six.iteritems(self.__dict__)]))

    @property
    def listing(self):
        now = Environment.get_instance().calendar_dt
        return self.listed_date <= now <= self.de_listed_date

    def days_from_listed(self):
        if self.listed_date == self.DEFAULT_LISTED_DATE:
            return -1

        date = Environment.get_instance().trading_dt.date()
        if self.de_listed_date.date() < date:
            return -1

        ipo_days = (date - self.listed_date.date()).days
        return ipo_days if ipo_days >= 0 else -1

    @property
    def enum_type(self):
        return instrument_type_str2enum(self.type)

    def days_to_expire(self):
        if self.type != 'Future' or self.order_book_id[-2:] == '88' or self.order_book_id[-2:] == '99':
            return -1

        date = Environment.get_instance().trading_dt.date()
        days = (self.maturity_date.date() - date).days
        return -1 if days < 0 else days


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
