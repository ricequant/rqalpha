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

from typing import List, Optional, Iterable, Dict, Union
from datetime import datetime

from typing_extensions import deprecated

from rqalpha.model.instrument import Instrument
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import InstrumentNotFound
from rqalpha.const import INSTRUMENT_TYPE

from rqalpha.interface import AbstractDataSource


class InstrumentsMixin:
    def __init__(self, data_source: AbstractDataSource):
        self._data_source = data_source

    @lru_cache(2048)
    def get_active_instrument(self, id_or_sym: str, dt: datetime) -> Instrument:
        """获取指定时间点上市的合约对象。

        :param id_or_sym: 合约代码或 order_book_id
        :param dt: 指定时间点
        :returns: 合约对象
        :raises InstrumentNotFound: 找不到合约或找到多个合约时抛出
        """
        candidates = []
        for instrument in self._data_source.get_instruments(id_or_syms=[id_or_sym]):
            if dt is None or instrument.active_at(dt):
                candidates.append(instrument)
        if not candidates:
            raise InstrumentNotFound(_("No instrument found at {dt}: {id_or_sym}").format(dt=dt, id_or_sym=id_or_sym))
        if len(candidates) > 1:
            raise InstrumentNotFound(_("Multiple instruments found at {dt}: {id_or_sym}").format(dt=dt, id_or_sym=id_or_sym))
        return candidates[0]

    @lru_cache(2048)
    def get_instrument_history(self, id_or_sym: str) -> List[Instrument]:
        """获取合约历史记录列表（包括已退市的合约）。

        :param id_or_sym: 合约代码或 order_book_id
        :returns: 合约对象列表
        """
        return list(self._data_source.get_instruments(id_or_syms=[id_or_sym]))

    def get_listed_instruments(self, id_or_syms: Iterable[str], dt: datetime) -> Dict[str, Instrument]:
        """批量获取指定时间点上市的合约对象。

        :param id_or_syms: 合约代码或 order_book_id 的可迭代对象
        :param dt: 指定时间点
        :returns: order_book_id 到合约对象的字典
        """
        result = {}
        ins_iter = self._data_source.get_instruments(id_or_syms=id_or_syms)
        for ins in ins_iter:
            if ins.active_at(dt):
                result[ins.order_book_id] = ins
        return result

    def get_all_instruments(self, types: List[INSTRUMENT_TYPE], dt: Optional[datetime] = None) -> List[Instrument]:
        """获取指定类型的所有合约。

        :param types: 合约类型列表
        :param dt: 可选，指定时间点，若提供则只返回该时间点上市的合约
        :returns: 合约对象列表
        """
        li = []
        for i in self._data_source.get_instruments(types=types):
            if dt is None or i.active_at(dt):
                li.append(i)
        return li

    @lru_cache(2048)
    def assure_order_book_id(self, order_book_id: str, expected_type: Optional[INSTRUMENT_TYPE] = None) -> str:
        """确保返回有效的 order_book_id。

        :param order_book_id: 合约代码或 order_book_id
        :param expected_type: 可选，期望的合约类型
        :returns: 标准化的 order_book_id
        :raises InstrumentNotFound: 找不到合约时抛出
        """
        for instrument in self._data_source.get_instruments(id_or_syms=[order_book_id]):
            if expected_type is not None and instrument.type != expected_type:
                continue
            return instrument.order_book_id
        raise InstrumentNotFound(_("No instrument found: {}").format(order_book_id))

    # ======================== DEPRECATED API ========================
    # 以下 API 已废弃，请逐步迁移到上方的新 API：
    #   - all_instruments -> get_all_instruments
    #   - instrument_not_none -> get_listed_instrument 或 get_instrument_history
    #   - instrument -> get_instrument_history
    #   - instruments -> get_listed_instruments 或 get_instrument_history
    # 原因
    #   旧版本的 RQAlpha 假设每个 order_book_id 只对应唯一的 Instrument 对象，但实际上存在代码复用的情况（如港股）；
    #   上述新 API 统一了命名规则，同时遵循 order_book_id + trading_date 才能唯一定位 Instrument 这一原则。
    # ================================================================

    @deprecated("Use get_all_instruments instead", category=None)
    def all_instruments(self, types: List[INSTRUMENT_TYPE], dt: Optional[datetime] = None) -> List[Instrument]:
        return self.get_all_instruments(types, dt)

    @deprecated("Use get_listed_instrument or get_instrument_history instead", category=None)
    def instrument_not_none(self, id_or_sym: str) -> Instrument:
        ins = self.get_instrument_history(id_or_sym)
        if not ins:
            raise InstrumentNotFound(_("No instrument found: {}").format(id_or_sym))
        return ins[0]

    @deprecated("Use get_instrument_history instead", category=None)
    def instrument(self, sym_or_id):
        ins = self.get_instrument_history(sym_or_id)
        if not ins:
            return None
        return ins[0]

    @deprecated("Use get_listed_instruments or get_instrument_history instead", category=None)
    def instruments(self, sym_or_ids: Union[str, Iterable[str]]) -> Union[None, Instrument, List[Instrument]]:
        if isinstance(sym_or_ids, str):
            return self.instrument(sym_or_ids)
        else:
            return list(self._data_source.get_instruments(id_or_syms=sym_or_ids))
