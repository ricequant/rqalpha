import datetime
import os
import h5py
from itertools import chain
from typing import Optional, List
from collections import defaultdict

import numpy as np
import pandas as pd

from rqalpha.apis.api_rqdatac import rqdatac
from rqalpha.utils.concurrent import ProgressedTask
from rqalpha.utils.datetime_func import convert_date_to_date_int, convert_date_to_int
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import system_log
from rqalpha.data.bundle.utils import mark_update_failed, START_DATE, END_DATE


class DayBarTask(ProgressedTask):
    def __init__(self, order_book_ids, file_path: str, fields: List[str], market="cn", **h5_kwargs):
        self._order_book_ids = order_book_ids
        self._init_instruments(order_book_ids)
        self._file_path = file_path
        self._fields = fields
        self._h5_kwargs = h5_kwargs
        self._market = market

    @property
    def total_steps(self) -> int:
        return len(self._order_book_ids)
    
    def _init_instruments(self, order_book_ids: List[str]):
        self._instruments = defaultdict(list)
        ints = rqdatac.instruments(order_book_ids)
        if not isinstance(ints, list):
            ints = [ints]
        for ins in ints:
            self._instruments[ins.order_book_id].append(ins)

    def _transfrom_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[self._fields]  # Future order_book_id like SC888 will auto add 'dominant_id'
        df.reset_index(inplace=True)
        df['datetime'] = [convert_date_to_int(d) for d in df['date']]
        del df['date']
        df.set_index(['order_book_id', 'datetime'], inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def _full_update(self, order_book_ids: List[str], h5: h5py.File):
        i, step = 0, 300
        while True:
            _oids = order_book_ids[i: i + step]
            df: Optional[pd.DataFrame] = rqdatac.get_price(
                _oids, START_DATE, END_DATE, '1d', adjust_type='none',
                fields=self._fields, expect_df=True, market=self._market
            )
            if not (df is None or df.empty):
                df = self._transfrom_df(df)
                for order_book_id in df.index.get_level_values("order_book_id").unique():
                    if order_book_id in h5:
                        del h5[order_book_id]
                    h5.create_dataset(order_book_id, data=df.loc[order_book_id].to_records(), **self._h5_kwargs)
            i += step
            yield len(_oids)
            if i >= len(order_book_ids):
                break

    def __call__(self):
        raise NotImplementedError


class GenerateDayBarTask(DayBarTask):
    def __call__(self):
        try:
            h5 = h5py.File(self._file_path, "w")
        except OSError:
            system_log.error("File {} update failed, if it is using, please update later, "
                            "or you can delete then update again".format(self._file_path))
            mark_update_failed()
            yield 1
        else:
            with h5:
                yield from self._full_update(self._order_book_ids, h5)


class UpdateDayBarTask(DayBarTask):
    def h5_has_valid_fields(self, h5, wanted_fields):
        obid_gen = (k for k in h5.keys())
        wanted_fields = set(wanted_fields)
        wanted_fields.add('datetime')
        try:
            h5_fields = set(h5[next(obid_gen)].dtype.fields.keys())
        except StopIteration:
            pass
        else:
            return h5_fields == wanted_fields
        return False

    def __call__(self):
        need_recreate_h5 = False
        try:
            with h5py.File(self._file_path, 'r') as h5:
                need_recreate_h5 = not self.h5_has_valid_fields(h5, self._fields)
        except (OSError, RuntimeError):
            need_recreate_h5 = True
        if need_recreate_h5:
            yield from GenerateDayBarTask(self._order_book_ids, self._file_path, self._fields, self._market, **self._h5_kwargs)()
        else:
            h5 = None
            try:
                h5 = h5py.File(self._file_path, 'a')
            except OSError:
                system_log.error("File {} update failed, if it is using, please update later, "
                                "or you can delete then update again".format(self._file_path))
                mark_update_failed()
                yield 1
            else:
                full_update_list = []
                skip_update_list = []  # 例如行情已经更新到停牌日期的标的
                incremental_update_dic = {}
                min_last_date = None  # h5 中最小的 last_date，作为 rqdatac.get_price 的 start_date
                is_futures = "futures" == os.path.basename(self._file_path).split(".")[0]
                for order_book_id in self._order_book_ids:
                    # 特殊处理前复权合约，需要全量更新
                    is_pre = is_futures and "888" in order_book_id
                    if order_book_id not in h5 or is_pre:
                        full_update_list.append(order_book_id)
                    else:
                        try:
                            last_date = int(h5[order_book_id]['datetime'][-1] // 1000000)  # type: ignore
                        except ValueError:
                            h5.pop(order_book_id)
                            full_update_list.append(order_book_id)
                        else:
                            ins = self._instruments[order_book_id]
                            de_listed_date = ins[0].de_listed_date if len(ins) == 1 else np.array([i.de_listed_date for i in ins]).max()
                            if de_listed_date != '0000-00-00':
                                if convert_date_to_date_int(rqdatac.get_previous_trading_date(de_listed_date)) <= last_date:
                                    skip_update_list.append(order_book_id)
                                    continue
                            min_last_date = min(last_date, min_last_date or last_date)
                            incremental_update_dic[order_book_id] = last_date
                
                if skip_update_list:
                    yield (len(skip_update_list))

                if full_update_list:
                    yield from self._full_update(full_update_list, h5)
                
                today = datetime.date.today()
                prev_trading_date = convert_date_to_int(rqdatac.get_previous_trading_date(today))
                if min_last_date == today or (not rqdatac.is_trading_date(today) and min_last_date == prev_trading_date):
                    yield len(incremental_update_dic.keys())
                else:
                    incremental = pd.Series(incremental_update_dic).sort_values()
                    i, step = 0, 300
                    while True:
                        incremental_slice = incremental.iloc[i: i + step]
                        order_book_ids = incremental_slice.index.tolist()
                        start_date = rqdatac.get_next_trading_date(int(incremental_slice.min()))
                        df = rqdatac.get_price(
                            order_book_ids, start_date, END_DATE, '1d', adjust_type='none',
                            fields=self._fields, expect_df=True, market=self._market
                        )
                        if not (df is None or df.empty):
                            df = self._transfrom_df(df)
                            for order_book_id in df.index.get_level_values("order_book_id").unique():
                                data = df.loc[order_book_id]
                                last_date = incremental_update_dic[order_book_id]
                                data = data[data.index > last_date * 1e6]
                                if not data.empty:
                                    data = np.array(
                                        [tuple(i) for i in chain(h5[order_book_id][:], data.to_records())],
                                        dtype=h5[order_book_id].dtype
                                    )
                                    del h5[order_book_id]
                                    h5.create_dataset(order_book_id, data=data, **self._h5_kwargs)

                        i += step
                        yield len(order_book_ids)
                        if i >= len(incremental):
                            break

            finally:
                if h5:
                    h5.close()
