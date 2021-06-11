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

from bisect import bisect_right

import numpy as np

from rqalpha.utils.datetime_func import convert_date_to_int


PRICE_FIELDS = {
    'open', 'close', 'high', 'low', 'limit_up', 'limit_down', 'acc_net_value', 'unit_net_value'
}

FIELDS_REQUIRE_ADJUSTMENT = set(list(PRICE_FIELDS) + ['volume'])


def _factor_for_date(dates, factors, d):
    pos = bisect_right(dates, d)
    return factors[pos-1]


def adjust_bars(bars, ex_factors, fields, adjust_type, adjust_orig):
    if ex_factors is None or len(bars) == 0:
        return bars

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
        return bars

    factors = ex_cum_factors.take(dates.searchsorted(bars['datetime'], side='right') - 1)

    # 复权
    bars = np.copy(bars)
    factors /= base_adjust_rate
    if isinstance(fields, str):
        if fields in PRICE_FIELDS:
            bars[fields] *= factors
            return bars
        elif fields == 'volume':
            bars[fields] *= (1 / factors)
            return bars
        # should not got here
        return bars

    for f in bars.dtype.names:
        if f in PRICE_FIELDS:
            bars[f] *= factors
        elif f == 'volume':
            bars[f] *= (1 / factors)
    return bars
