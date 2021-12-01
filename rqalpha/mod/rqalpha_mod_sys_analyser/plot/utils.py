# -*- coding: utf-8 -*-
# 版权所有 2021 深圳米筐科技有限公司（下称“米筐科技”）
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

from collections import namedtuple

import numpy as np
from numpy import array
from pandas import DatetimeIndex, DataFrame, Series, to_datetime

IndicatorInfo = namedtuple("IndicatorInfo", ("key", "label", "color", "formatter", "value_font_size"))
LineInfo = namedtuple("LineInfo", ("label", "color", "alpha", "linewidth"))
SpotInfo = namedtuple("SpotInfo", ("label", "marker", "color", "markersize", "alpha"))


class IndexRange(namedtuple("IndexRange", ("start", "end", "start_date", "end_date"))):
    @classmethod
    def new(cls, start, end, index):
        return cls(start, end, index[start].date(), index[end].date())

    @property
    def repr(self):
        return "{}~{}, {} days".format(self.start_date, self.end_date, (self.end_date - self.start_date).days)


def max_dd(arr: array, index: DatetimeIndex) -> IndexRange:
    end = np.argmax(np.maximum.accumulate(arr) / arr)
    if end == 0:
        end = len(arr) - 1
    start = np.argmax(arr[:end]) if end > 0 else 0
    return IndexRange.new(start, end, index)


def max_ddd(arr: array, index: DatetimeIndex) -> IndexRange:
    max_seen = arr[0]
    ddd_start, ddd_end = 0, 0
    ddd = 0
    start = 0
    in_draw_down = False

    i = 0
    for i in range(len(arr)):
        if arr[i] > max_seen:
            if in_draw_down:
                in_draw_down = False
                if i - start > ddd:
                    ddd = i - start
                    ddd_start = start
                    ddd_end = i - 1
            max_seen = arr[i]
        elif arr[i] < max_seen:
            if not in_draw_down:
                in_draw_down = True
                start = i - 1

    if arr[i] < max_seen:
        if i - start > ddd:
            return IndexRange.new(start, i, index)

    return IndexRange.new(ddd_start, ddd_end, index)


def weekly_returns(portfolio: DataFrame) -> Series:
    return portfolio.unit_net_value.reset_index().resample(
        "W", on="date").last().set_index("date").unit_net_value.dropna() - 1


def trading_dates_index(trades: DataFrame, position_effect, index: DatetimeIndex):
    return index.searchsorted(
        to_datetime(trades[trades.position_effect == position_effect].trading_datetime), side="right"
    ) - 1
