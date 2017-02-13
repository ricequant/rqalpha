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

import pandas as pd
import six


class InstrumentMixin(object):
    def __init__(self, instruments):
        self._instruments = {i.order_book_id: i for i in instruments}
        self._sym_id_map = {i.symbol: k for k, i in six.iteritems(self._instruments)
                            # 过滤掉 CSI300, SSE50, CSI500, SSE180
                            if not i.order_book_id.endswith('INDX')}
        # 沪深300 中证500 固定使用上证的
        for o in ['000300.XSHG', '000905.XSHG']:
            self._sym_id_map[self._instruments[o].symbol] = o
        # 上证180 及 上证180指数 两个symbol都指向 000010.XSHG
        self._sym_id_map[self._instruments['SSE180.INDX'].symbol] = '000010.XSHG'

    def sector(self, code):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and v.sector_code == code]

    def industry(self, code):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and v.industry_code == code]

    def concept(self, *concepts):
        return [v.order_book_id for v in self._instruments.values()
                if v.type == 'CS' and any(c in v.concept_names.split('|') for c in concepts)]

    def all_instruments(self, itype='CS'):
        if itype is None:
            return pd.DataFrame([[v.order_book_id, v.symbol, v.abbrev_symbol, v.type]
                                 for v in self._instruments.values()],
                                columns=['order_book_id', 'symbol', 'abbrev_symbol', 'type'])

        if itype not in ['CS', 'ETF', 'LOF', 'FenjiA', 'FenjiB', 'FenjiMu', 'INDX', 'Future']:
            raise ValueError('Unknown type {}'.format(itype))

        return pd.DataFrame([v.__dict__ for v in self._instruments.values() if v.type == itype])

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
        if isinstance(sym_or_ids, six.string_types):
            return self._instrument(sym_or_ids)

        return [i for i in [self._instrument(sid) for sid in sym_or_ids] if i is not None]

    def get_future_contracts(self, underlying, date):
        futures = [v for o, v in six.iteritems(self._instruments)
                   if v.type == 'Future' and v.underlying_symbol == underlying and
                   not o.endswith('88') and not o.endswith('99')]
        if not futures:
            return []

        return sorted(i.order_book_id for i in futures if i.listed_date <= date <= i.de_listed_date)
