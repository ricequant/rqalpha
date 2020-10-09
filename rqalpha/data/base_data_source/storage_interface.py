# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
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

import abc
from typing import List, Optional, Sequence, Iterable

import numpy as np
import pandas

from rqalpha.model.instrument import Instrument
from rqalpha.utils.typing import DateLike
from rqalpha.const import INSTRUMENT_TYPE


class AbstractInstrumentStore:
    @property
    @abc.abstractmethod
    def instrument_type(self):
        # type: () -> INSTRUMENT_TYPE
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def all_id_and_syms(self):
        # type: () -> Iterable[str]
        raise NotImplementedError

    def get_instruments(self, id_or_syms):
        # type: (Optional[Iterable[str]]) -> Iterable[Instrument]
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


class AbstractDateSet:
    @abc.abstractmethod
    def contains(self, order_book_id, dates):
        # type: (str, Sequence[DateLike]) -> Optional[List[bool]]
        # 若 DateSet 中不包含该 order_book_id 的信息则返回 None，否则返回 List[bool]
        raise NotImplementedError


class AbstractDividendStore:
    @abc.abstractmethod
    def get_dividend(self, order_book_id):
        # type: (str) -> np.ndarray
        raise NotImplementedError


class AbstractSimpleFactorStore:
    @abc.abstractmethod
    def get_factors(self, order_book_id):
        # type: (str) -> np.ndarray
        raise NotImplementedError
