# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import abc
import codecs
import pickle
from copy import copy
from typing import List

import json
import pandas
import numpy as np

from rqalpha.utils.i18n import gettext as _
from rqalpha.const import COMMISSION_TYPE, INSTRUMENT_TYPE
from rqalpha.model.instrument import Instrument


class AbstractInstrumentStore:
    @abc.abstractmethod
    def get_all_instruments(self):
        # type: () -> List[Instrument]
        raise NotImplementedError


class AbstractDayBarStore:
    @abc.abstractmethod
    def get_bars(self, order_book_id):
        # type: (str) -> np.ndarray
        raise NotImplementedError

    def get_date_range(self, order_book_id):
        raise NotImplementedError


class AbstractCalendarStore:
    @abc.abstractmethod
    def get_trading_calendar(self):
        # type: () -> pandas.DatetimeIndex
        raise NotImplementedError


class ExchangeTradingCalendarStore(AbstractCalendarStore):
    def __init__(self, f):
        self._f = f

    def get_trading_calendar(self):
        # type: () -> pandas.DatetimeIndex
        return pandas.to_datetime([str(d) for d in np.load(self._f, allow_pickle=False)])


class FutureInfoStore(object):
    COMMISSION_TYPE_MAP = {
        "by_volume": COMMISSION_TYPE.BY_VOLUME,
        "by_money": COMMISSION_TYPE.BY_MONEY
    }

    def __init__(self, f, custom_future_info):
        with open(f, "r") as json_file:
            self._default_data = {
                item.get("order_book_id") or item.get("underlying_symbol"): self._process_future_info_item(
                    item
                ) for item in json.load(json_file)
            }
        self._custom_data = custom_future_info
        self._future_info = {}

    @classmethod
    def _process_future_info_item(cls, item):
        item["commission_type"] = cls.COMMISSION_TYPE_MAP[item["commission_type"]]
        return item

    def get_future_info(self, instrument):
        order_book_id = instrument.order_book_id
        try:
            return self._future_info[order_book_id]
        except KeyError:
            custom_info = self._custom_data.get(order_book_id) or self._custom_data.get(instrument.underlying_symbol)
            info = self._default_data.get(order_book_id) or self._default_data.get(instrument.underlying_symbol)
            if custom_info:
                info = copy(info) or {}
                info.update(custom_info)
            elif not info:
                raise NotImplementedError(_("unsupported future instrument {}").format(order_book_id))
            return self._future_info.setdefault(order_book_id, info)


class InstrumentStore(AbstractInstrumentStore):
    SUPPORTED_TYPES = (
        INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.INDX,
        INSTRUMENT_TYPE.FENJI_A, INSTRUMENT_TYPE.FENJI_B, INSTRUMENT_TYPE.FENJI_MU, INSTRUMENT_TYPE.PUBLIC_FUND,
    )

    def __init__(self, f):
        with open(f, 'rb') as store:
            d = pickle.load(store)

        self._instruments = []
        for i in d:
            ins = Instrument(i)
            if ins.type in self.SUPPORTED_TYPES:
                self._instruments.append(ins)

    def get_all_instruments(self):
        return self._instruments


class ShareTransformationStore(object):
    def __init__(self, f):
        with codecs.open(f, 'r', encoding="utf-8") as store:
            self._share_transformation = json.load(store)

    def get_share_transformation(self, order_book_id):
        try:
            transformation_data = self._share_transformation[order_book_id]
        except KeyError:
            return
        return transformation_data["successor"], transformation_data["share_conversion_ratio"]
