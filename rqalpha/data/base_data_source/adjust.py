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

import datetime
from bisect import bisect_right

import numpy as np

from rqalpha.utils.datetime_func import convert_date_to_int


PRICE_FIELDS = {
    'open', 'close', 'high', 'low', 'limit_up', 'limit_down', 'acc_net_value', 'unit_net_value'
}

FIELDS_REQUIRE_ADJUSTMENT = set(list(PRICE_FIELDS) + ['volume'])


def factor_for_date(ex_factors, date):
    """
    获取 date 当天的复权因子。

    :param ex_factors: 复权因子表，包含 start_date / ex_cum_factor 字段
    """
    if ex_factors is None or len(ex_factors) == 0:
        return 1.

    d = np.uint64(convert_date_to_int(date)) if isinstance(date, datetime.date) else date
    pos = bisect_right(ex_factors["start_date"], d)
    return ex_factors["ex_cum_factor"][pos - 1]


def adjust_rate(ex_factors, date, adjust_type, adjust_orig):
    """
    获取把「未复权的原始价」换算到与 adjust_bars 相同复权口径的比例
    数据源在 history_bars 之外自行拼接数据时，需要使用该比例换算

    :param date: 被换算的那根 bar 自身的日期
    :param adjust_orig: 复权起点，需要与 history_bars 的 adjust_orig 保持一致
    """
    if ex_factors is None or adjust_type == "none":
        return 1.

    if adjust_type == "pre":
        base_factor = factor_for_date(ex_factors, adjust_orig)
    else:
        base_factor = 1.
    return factor_for_date(ex_factors, date) / base_factor


def adjust_bars(bars, ex_factors, fields, adjust_type, adjust_orig):
    if ex_factors is None or len(bars) == 0:
        return bars

    if adjust_type == 'pre':
        base_adjust_rate = factor_for_date(ex_factors, adjust_orig)
    else:
        base_adjust_rate = 1.0

    start_date = bars['datetime'][0]
    end_date = bars['datetime'][-1]
    if factor_for_date(ex_factors, start_date) == base_adjust_rate and factor_for_date(ex_factors, end_date) == base_adjust_rate:
        return bars

    dates = ex_factors["start_date"]
    ex_cum_factors = ex_factors["ex_cum_factor"]
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
