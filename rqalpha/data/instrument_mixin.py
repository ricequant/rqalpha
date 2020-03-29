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

import re
import six
from datetime import datetime
from typing import Union, List, Iterable, Optional

from rqalpha.model.instrument import Instrument
from rqalpha.utils import merge_trading_period
from rqalpha.const import INSTRUMENT_TYPE


class InstrumentMixin(object):
    def __init__(self, instruments):
        self._instruments = {i.order_book_id: i for i in instruments}
        self._sym_id_map = {i.symbol: k for k, i in six.iteritems(self._instruments)
                            # 过滤掉 CSI300, SSE50, CSI500, SSE180
                            if not i.order_book_id.endswith('INDX')}
        try:
            # FIXME
            # 沪深300 中证500 固定使用上证的
            for o in ['000300.XSHG', '000905.XSHG']:
                self._sym_id_map[self._instruments[o].symbol] = o
            # 上证180 及 上证180指数 两个symbol都指向 000010.XSHG
            self._sym_id_map[self._instruments['SSE180.INDX'].symbol] = '000010.XSHG'
        except KeyError:
            pass

    def all_instruments(self, types, dt=None):
        # type: (List[INSTRUMENT_TYPE], Optional[datetime]) -> List[Instrument]
        return [i for i in self._instruments.values() if ((
            dt is None or i.listing_at(dt)
        ) and (
            types is None or i.type in types
        ))]

    def _instrument(self, sym_or_id):
        try:
            return self._instruments[sym_or_id]
        except KeyError:
            try:
                sym_or_id = self._sym_id_map[sym_or_id]
                return self._instruments[sym_or_id]
            except KeyError:
                return None

    def instruments(self, sym_or_ids):
        # type: (Union[str, Iterable[str]]) -> Union[Instrument, List[Instrument]]
        if isinstance(sym_or_ids, six.string_types):
            return self._instrument(sym_or_ids)

        return [i for i in [self._instrument(sid) for sid in sym_or_ids] if i is not None]

    CONTINUOUS_CONTRACT = re.compile("^[A-Z]{1,2}(88|888|99|889)$")

    def get_future_contracts(self, underlying, date):
        date = date.replace(hour=0, minute=0, second=0)
        futures = [v for o, v in six.iteritems(
            self._instruments
        ) if v.type == 'Future' and v.underlying_symbol == underlying and not re.match(self.CONTINUOUS_CONTRACT, o)]
        if not futures:
            return []

        return sorted(i.order_book_id for i in futures if i.listed_date <= date <= i.de_listed_date)

    def get_trading_period(self, sym_or_ids, default_trading_period=None):
        trading_period = default_trading_period or []
        for instrument in self.instruments(sym_or_ids):
            trading_period.extend(instrument.trading_hours or [])
        return merge_trading_period(trading_period)

    def is_night_trading(self, sym_or_ids):
        return any((instrument.trade_at_night for instrument in self.instruments(sym_or_ids)))
