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

import bcolz
import numpy as np


class DividendStore(object):
    def __init__(self, f):
        ct = bcolz.open(f, 'r')
        self._index = ct.attrs['line_map']
        self._table = np.empty((len(ct), ), dtype=np.dtype([
            ('announcement_date', '<u4'), ('book_closure_date', '<u4'),
            ('ex_dividend_date', '<u4'), ('payable_date', '<u4'),
            ('dividend_cash_before_tax', np.float), ('round_lot', '<u4')
        ]))
        self._table['announcement_date'][:] = ct['announcement_date']
        self._table['book_closure_date'][:] = ct['closure_date']
        self._table['ex_dividend_date'][:] = ct['ex_date']
        self._table['payable_date'][:] = ct['payable_date']
        self._table['dividend_cash_before_tax'] = ct['cash_before_tax'][:] / 10000.0
        self._table['round_lot'][:] = ct['round_lot']

    def get_dividend(self, order_book_id):
        try:
            s, e = self._index[order_book_id]
        except KeyError:
            return None

        return self._table[s:e]
