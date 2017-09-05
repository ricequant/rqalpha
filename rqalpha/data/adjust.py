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
from bisect import bisect_right

import numpy as np

from rqalpha.utils.datetime_func import convert_date_to_int


PRICE_FIELDS = {
    'open', 'close', 'high', 'low', 'limit_up', 'limit_down', 'acc_net_value', 'unit_net_value'
}

FIELDS_REQUIRE_ADJUSTMENT = set(list(PRICE_FIELDS) + ['volume'])


def _factor_for_date(dates, factors, d):
    if d < dates[0]:
        return 1
    if d > dates[-1]:
        return factors[-1]
    pos = bisect_right(dates, d)
    return factors[pos-1]


def adjust_bars(bars, ex_factors, fields, adjust_type, adjust_orig):
    if ex_factors is None or len(bars) == 0:
        return bars if fields is None else bars[fields]

    dates = ex_factors['start_date']
    ex_cum_factors = ex_factors['ex_cum_factor']

    if adjust_type == 'pre':
        adjust_orig_dt = np.uint64(convert_date_to_int(adjust_orig))
        base_adjust_rate = _factor_for_date(dates, ex_cum_factors, adjust_orig_dt)
    else:
        base_adjust_rate = 1.0

    start_date = bars['datetime'][0]
    end_date = bars['datetime'][-1]

    if (_factor_for_date(dates, ex_cum_factors, start_date) == base_adjust_rate and
            _factor_for_date(dates, ex_cum_factors, end_date) == base_adjust_rate):
        return bars if fields is None else bars[fields]

    factors = ex_cum_factors.take(dates.searchsorted(bars['datetime'], side='right') - 1)

    # 复权
    factors /= base_adjust_rate
    if isinstance(fields, str):
        if fields in PRICE_FIELDS:
            return bars[fields] * factors
        elif fields == 'volume':
            return bars[fields] * (1 / factors)
        # should not got here
        return bars[fields]

    result = np.copy(bars if fields is None else bars[fields])
    for f in result.dtype.names:
        if f in PRICE_FIELDS:
            result[f] *= factors
        elif f == 'volume':
            result[f] *= (1 / factors)
    return result
