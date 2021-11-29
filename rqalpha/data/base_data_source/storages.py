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

import codecs
import json
import locale
import os
import sys
from copy import copy
from itertools import chain
from contextlib import contextmanager
from typing import Dict, Iterable, Optional

import h5py
import numpy as np
import pandas
from rqalpha.const import COMMISSION_TYPE, INSTRUMENT_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils.datetime_func import convert_date_to_date_int
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _

from .storage_interface import (AbstractCalendarStore, AbstractDateSet,
                                AbstractDayBarStore, AbstractDividendStore,
                                AbstractInstrumentStore,
                                AbstractSimpleFactorStore)


class ExchangeTradingCalendarStore(AbstractCalendarStore):
    def __init__(self, f):
        self._f = f

    def get_trading_calendar(self):
        # type: () -> pandas.DatetimeIndex
        return pandas.to_datetime([str(d) for d in np.load(self._f, allow_pickle=False)])


class FutureInfoStore(object):
    COMMISSION_TYPE_MAP = {
        "by_volume": COMMISSION_TYPE.BY_VOLUME,
        "by_money": COMMISSION_TYPE.BY_MONEY
    }

    def __init__(self, f, custom_future_info):
        with open(f, "r") as json_file:
            self._default_data = {
                item.get("order_book_id") or item.get("underlying_symbol"): self._process_future_info_item(
                    item
                ) for item in json.load(json_file)
            }
        self._custom_data = custom_future_info
        self._future_info = {}

    @classmethod
    def _process_future_info_item(cls, item):
        item["commission_type"] = cls.COMMISSION_TYPE_MAP[item["commission_type"]]
        return item

    def get_future_info(self, instrument):
        # type: (Instrument) -> Dict[str, float]
        order_book_id = instrument.order_book_id
        try:
            return self._future_info[order_book_id]
        except KeyError:
            custom_info = self._custom_data.get(order_book_id) or self._custom_data.get(instrument.underlying_symbol)
            info = self._default_data.get(order_book_id) or self._default_data.get(instrument.underlying_symbol)
            if custom_info:
                info = copy(info) or {}
                info.update(custom_info)
            elif not info:
                raise NotImplementedError(_("unsupported future instrument {}").format(order_book_id))
            return self._future_info.setdefault(order_book_id, info)


class InstrumentStore(AbstractInstrumentStore):
    def __init__(self, instruments, instrument_type):
        # type: (Iterable[Instrument], INSTRUMENT_TYPE) -> None
        self._instrument_type = instrument_type
        self._instruments = {}
        self._sym_id_map = {}

        for ins in instruments:
            if ins.type != instrument_type:
                continue
            self._instruments[ins.order_book_id] = ins
            self._sym_id_map[ins.symbol] = ins.order_book_id

    @property
    def instrument_type(self):
        # type: () -> INSTRUMENT_TYPE
        return self._instrument_type

    @property
    def all_id_and_syms(self):
        # type: () -> Iterable[str]
        return chain(self._instruments.keys(), self._sym_id_map.keys())

    def get_instruments(self, id_or_syms):
        # type: (Optional[Iterable[str]]) -> Iterable[Instrument]
        if id_or_syms is None:
            return self._instruments.values()
        order_book_ids = set()
        for i in id_or_syms:
            if i in self._instruments:
                order_book_ids.add(i)
            elif i in self._sym_id_map:
                order_book_ids.add(self._sym_id_map[i])
        return (self._instruments[i] for i in order_book_ids)


class ShareTransformationStore(object):
    def __init__(self, f):
        with codecs.open(f, 'r', encoding="utf-8") as store:
            self._share_transformation = json.load(store)

    def get_share_transformation(self, order_book_id):
        try:
            transformation_data = self._share_transformation[order_book_id]
        except KeyError:
            return
        return transformation_data["successor"], transformation_data["share_conversion_ratio"]


def _file_path(path):
    # why do this? non-ascii path in windows!!
    if sys.platform == "win32":
        try:
            l = locale.getlocale(locale.LC_ALL)[1]
        except TypeError:
            l = None
        if l and l.lower() == "utf-8":
            return path.encode("utf-8")
    return path


def open_h5(path, *args, **kwargs):
    # forward compatible
    try:
        return h5py.File(_file_path(path), *args, **kwargs)
    except OSError as e:
        raise RuntimeError(_(
            "open data bundle failed, you can remove {} and try to regenerate bundle: {}"
        ).format(path, e))


@contextmanager
def h5_file(path, *args, mode="r", **kwargs):
    try:
        h5 = h5py.File(_file_path(path), *args, mode=mode, **kwargs)
    except OSError as e:
        raise RuntimeError(_(
            "open data bundle failed, you can remove {} and try to regenerate bundle: {}"
        ).format(path, e))
    else:
        try:
            yield h5
        finally:
            h5.close()


class DayBarStore(AbstractDayBarStore):
    DEFAULT_DTYPE = np.dtype([
        ('datetime', np.uint64),
        ('open', np.float),
        ('close', np.float),
        ('high', np.float),
        ('low', np.float),
        ('volume', np.float),
    ])

    def __init__(self, path):
        if not os.path.exists(path):
            raise FileExistsError("File {} not exist，please update bundle.".format(path))
        self._path = path

    def get_bars(self, order_book_id):
        with h5_file(self._path) as h5:
            try:
                return h5[order_book_id][:]
            except KeyError:
                return np.empty(0, dtype=self.DEFAULT_DTYPE)

    def get_date_range(self, order_book_id):
        with h5_file(self._path) as h5:
            try:
                data = h5[order_book_id]
                return data[0]['datetime'], data[-1]['datetime']
            except KeyError:
                return 20050104, 20050104


class FutureDayBarStore(DayBarStore):
    DEFAULT_DTYPE = np.dtype(DayBarStore.DEFAULT_DTYPE.descr + [("open_interest", '<f8')])


class DividendStore(AbstractDividendStore):
    def __init__(self, path):
        self._path = path

    def get_dividend(self, order_book_id):
        with h5_file(self._path) as h5:
            try:
                return h5[order_book_id][:]
            except KeyError:
                return None


class YieldCurveStore:
    def __init__(self, path):
        with h5_file(path) as h5:
            self._data = h5["data"][:]

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

        df = pandas.DataFrame(self._data[s:e])
        df.index = pandas.to_datetime([str(d) for d in df['date']])
        del df['date']

        if tenor is not None:
            return df[tenor]
        return df


class SimpleFactorStore(AbstractSimpleFactorStore):
    def __init__(self, path):
        self._path = path

    def get_factors(self, order_book_id):
        with h5_file(self._path) as h5:
            try:
                return h5[order_book_id][:]
            except KeyError:
                return None


class DateSet(AbstractDateSet):
    def __init__(self, f):
        self._f = f

    @lru_cache(None)
    def get_days(self, order_book_id):
        with h5_file(self._f) as h5:
            try:
                days = h5[order_book_id][:]
            except KeyError:
                return set()
            return set(days.tolist())

    def contains(self, order_book_id, dates):
        date_set = self.get_days(order_book_id)
        if not date_set:
            return None

        def _to_dt_int(d):
            if isinstance(d, (int, np.int64, np.uint64)):
                return int(d // 1000000) if d > 100000000 else int(d)
            else:
                return d.year * 10000 + d.month * 100 + d.day

        return [(_to_dt_int(d) in date_set) for d in dates]
