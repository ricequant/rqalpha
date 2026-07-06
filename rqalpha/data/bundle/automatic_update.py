import datetime
import os
from itertools import chain
from typing import Callable, Optional, Union, List
from filelock import FileLock, Timeout

import h5py
import numpy as np
from rqalpha.utils.datetime_func import convert_date_to_date_int
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.functools import lru_cache
from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument
from rqalpha.data.bundle.utils import START_DATE


class AutomaticUpdateBundle(object):
    def __init__(self, path: str, filename: str, api: Callable, fields: List[str], end_date: datetime.date, start_date: Union[int, datetime.date] = START_DATE) -> None:
        if not os.path.exists(path):
            os.makedirs(path)
        self._file = os.path.join(path, filename)
        self._trading_dates = None
        self._filename = filename
        self._api = api
        self._fields = fields
        self._start_date = start_date
        self.updated = []
        self._env = Environment.get_instance()
        self._file_lock = FileLock(self._file + ".lock")

    def get_data(self, instrument: Instrument, dt: datetime.date) -> Optional[np.ndarray]:
        dt_int = convert_date_to_date_int(dt)
        data = self._get_data_all_time(instrument)
        if data is None:
            return data
        else:
            try:
                data = data[np.searchsorted(data['trading_dt'], dt_int)]
            except IndexError:
                data = None
            return data

    @lru_cache(128)
    def _get_data_all_time(self, instrument: Instrument) -> Optional[np.ndarray]:
        if instrument.order_book_id not in self.updated:
            self._auto_update_task(instrument)
            self.updated.append(instrument.order_book_id)
        with h5py.File(self._file, "r") as h5:
            data = h5[instrument.order_book_id][:]
            if len(data) == 0:
                return None
        return data

    def _auto_update_task(self, instrument: Instrument) -> None:
        """
        在 rqalpha 策略运行过程中自动更新所需的日线数据

        :param instrument: 合约对象
        :type instrument: `Instrument`
        """
        order_book_id = instrument.order_book_id
        start_date = self._start_date
        h5 = None
        try:
            with self._file_lock.acquire():
                h5 = h5py.File(self._file, "a")
                if order_book_id in h5 and h5[order_book_id].dtype.names:
                    if 'trading_dt' in h5[order_book_id].dtype.names:
                        # 需要兼容此前的旧版数据，对字段名进行更新
                        if len(h5[order_book_id][:]) != 0:
                            last_date = datetime.datetime.strptime(str(h5[order_book_id][-1]['trading_dt']), "%Y%m%d").date()
                            if last_date >= self._env.config.base.end_date:
                                return
                            start_date = self._env.data_proxy._data_source.get_next_trading_date(last_date).date()
                            if start_date > self._env.config.base.end_date:
                                return
                    else:
                        del h5[order_book_id]

                arr = self._get_array(instrument, start_date)
                if arr is None:
                    if order_book_id not in h5:
                        arr = np.array([])
                        h5.create_dataset(order_book_id, data=arr)
                else:
                    if order_book_id in h5:
                        data = np.array(
                            [tuple(i) for i in chain(h5[order_book_id][:], arr)],
                            dtype=h5[order_book_id].dtype)
                        del h5[order_book_id]
                        h5.create_dataset(order_book_id, data=data)
                    else:
                        h5.create_dataset(order_book_id, data=arr)
        except (OSError, Timeout) as e:
            raise OSError(_("File {} update failed, if it is using, please update later, "
                          "or you can delete then update again".format(self._file))) from e
        finally:
            if h5:
                h5.close()

    def _get_array(self, instrument: Instrument, start_date: Union[datetime.date, int]) -> Optional[np.ndarray]:
        df = self._api(instrument.order_book_id, start_date, self._env.config.base.end_date, self._fields)
        if not (df is None or df.empty):
            df = df[self._fields].loc[instrument.order_book_id] # rqdatac.get_open_auction_info get Futures's data will auto add 'open_interest' and 'prev_settlement'
            record = df.iloc[0: 1].to_records()
            dtype = [('trading_dt', 'int')]
            for field in self._fields:
                dtype.append((field, record.dtype[field]))
            trading_dt = self._env.data_proxy._data_source.batch_get_trading_date(df.index)
            trading_dt = convert_date_to_date_int(trading_dt)
            arr = np.ones((trading_dt.shape[0], ), dtype=dtype)
            arr['trading_dt'] = trading_dt
            for field in self._fields:
                arr[field] = df[field].values
            return arr
        return None