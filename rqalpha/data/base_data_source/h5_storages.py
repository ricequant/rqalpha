# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import numpy as np
import pandas as pd

from rqalpha.utils.datetime_func import convert_date_to_date_int

from .storages import AbstractDayBarStore
from .date_set import open_h5


DEFAULT_DTYPE = np.dtype([
    ('datetime', np.uint64),
    ('open', np.float),
    ('close', np.float),
    ('high', np.float),
    ('low', np.float),
    ('volume', np.float),
])


class DayBarStore(AbstractDayBarStore):
    def __init__(self, path):
        self._h5 = open_h5(path, mode="r")

    def get_bars(self, order_book_id):
        try:
            return self._h5[order_book_id][:]
        except KeyError:
            return np.empty(0, dtype=DEFAULT_DTYPE)

    def get_date_range(self, order_book_id):
        try:
            data = self._h5[order_book_id]
            return data[0]['datetime'], data[-1]['datetime']
        except KeyError:
            return 20050104, 20050104


class DividendStore:
    def __init__(self, path):
        self._h5 = open_h5(path, mode="r")

    def get_dividend(self, order_book_id):
        try:
            return self._h5[order_book_id][:]
        except KeyError:
            return None


class YieldCurveStore:
    def __init__(self, path):
        self._data = open_h5(path, mode="r")["data"][:]

    def get_yield_curve(self, start_date, end_date, tenor):
        d1 = convert_date_to_date_int(start_date)
        d2 = convert_date_to_date_int(end_date)

        s = self._data['date'].searchsorted(d1)
        e = self._data['date'].searchsorted(d2, side='right')

        if e == len(self._data):
            e -= 1
        if self._data[e]['date'] == d2:
            e += 1

        if e < s:
            return None

        df = pd.DataFrame(self._data[s:e])
        df.index = pd.to_datetime([str(d) for d in df['date']])
        del df['date']

        if tenor is not None:
            return df[tenor]
        return df


class SimpleFactorStore:
    def __init__(self, path):
        self._h5 = open_h5(path, mode="r")

    def get_factors(self, order_book_id):
        try:
            return self._h5[order_book_id][:]
        except KeyError:
            return None
