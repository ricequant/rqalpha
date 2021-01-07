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
import datetime
import json
import os
import pickle
import re
from itertools import chain

import h5py
import numpy as np
from rqalpha.apis.api_rqdatac import rqdatac
from rqalpha.utils.concurrent import (ProgressedProcessPoolExecutor,
                                      ProgressedTask)
from rqalpha.utils.datetime_func import (convert_date_to_date_int,
                                         convert_date_to_int)

START_DATE = 20050104
END_DATE = 29991231


def gen_instruments(d):
    stocks = sorted(list(rqdatac.all_instruments().order_book_id))
    instruments = [i.__dict__ for i in rqdatac.instruments(stocks)]
    with open(os.path.join(d, 'instruments.pk'), 'wb') as out:
        pickle.dump(instruments, out, protocol=2)


def gen_yield_curve(d):
    yield_curve = rqdatac.get_yield_curve(start_date=START_DATE, end_date=datetime.date.today())
    yield_curve.index = [convert_date_to_date_int(d) for d in yield_curve.index]
    yield_curve.index.name = 'date'
    with h5py.File(os.path.join(d, 'yield_curve.h5'), 'w') as f:
        f.create_dataset('data', data=yield_curve.to_records())


def gen_trading_dates(d):
    dates = rqdatac.get_trading_dates(start_date=START_DATE, end_date='2999-01-01')
    dates = np.array([convert_date_to_date_int(d) for d in dates])
    np.save(os.path.join(d, 'trading_dates.npy'), dates, allow_pickle=False)


def gen_st_days(d):
    from rqdatac.client import get_client
    stocks = rqdatac.all_instruments('CS').order_book_id.tolist()
    st_days = get_client().execute('get_st_days', stocks, START_DATE,
                                   convert_date_to_date_int(datetime.date.today()))
    with h5py.File(os.path.join(d, 'st_stock_days.h5'), 'w') as h5:
        for order_book_id, days in st_days.items():
            h5[order_book_id] = days


def gen_suspended_days(d):
    from rqdatac.client import get_client
    stocks = rqdatac.all_instruments('CS').order_book_id.tolist()
    suspended_days = get_client().execute('get_suspended_days', stocks, START_DATE,
                                          convert_date_to_date_int(datetime.date.today()))
    with h5py.File(os.path.join(d, 'suspended_days.h5'), 'w') as h5:
        for order_book_id, days in suspended_days.items():
            h5[order_book_id] = days


def gen_dividends(d):
    stocks = rqdatac.all_instruments().order_book_id.tolist()
    dividend = rqdatac.get_dividend(stocks)
    dividend.reset_index(inplace=True)
    dividend.rename(columns={'declaration_announcement_date': 'announcement_date'}, inplace=True)
    for f in ('book_closure_date', 'ex_dividend_date', 'payable_date', 'announcement_date'):
        dividend[f] = [convert_date_to_date_int(d) for d in dividend[f]]
    dividend.set_index(['order_book_id', 'book_closure_date'], inplace=True)
    with h5py.File(os.path.join(d, 'dividends.h5'), 'w') as h5:
        for order_book_id in dividend.index.levels[0]:
            h5[order_book_id] = dividend.loc[order_book_id].to_records()


def gen_splits(d):
    stocks = rqdatac.all_instruments().order_book_id.tolist()
    split = rqdatac.get_split(stocks)
    split['split_factor'] = split['split_coefficient_to'] / split['split_coefficient_from']
    split = split[['split_factor']]
    split.reset_index(inplace=True)
    split.rename(columns={'ex_dividend_date': 'ex_date'}, inplace=True)
    split['ex_date'] = [convert_date_to_int(d) for d in split['ex_date']]
    split.set_index(['order_book_id', 'ex_date'], inplace=True)

    with h5py.File(os.path.join(d, 'split_factor.h5'), 'w') as h5:
        for order_book_id in split.index.levels[0]:
            h5[order_book_id] = split.loc[order_book_id].to_records()


def gen_ex_factor(d):
    stocks = rqdatac.all_instruments().order_book_id.tolist()
    ex_factor = rqdatac.get_ex_factor(stocks)
    ex_factor.reset_index(inplace=True)
    ex_factor['ex_date'] = [convert_date_to_int(d) for d in ex_factor['ex_date']]
    ex_factor.rename(columns={'ex_date': 'start_date'}, inplace=True)
    ex_factor.set_index(['order_book_id', 'start_date'], inplace=True)
    ex_factor = ex_factor[['ex_cum_factor']]

    dtype = ex_factor.loc[ex_factor.index.levels[0][0]].to_records().dtype
    initial = np.empty((1,), dtype=dtype)
    initial['start_date'] = 0
    initial['ex_cum_factor'] = 1.0

    with h5py.File(os.path.join(d, 'ex_cum_factor.h5'), 'w') as h5:
        for order_book_id in ex_factor.index.levels[0]:
            h5[order_book_id] = np.concatenate([initial, ex_factor.loc[order_book_id].to_records()])


def gen_share_transformation(d):
    df = rqdatac.get_share_transformation()
    df.drop_duplicates("predecessor", inplace=True)
    df.set_index('predecessor', inplace=True)
    df.effective_date = df.effective_date.astype(str)
    df.predecessor_delisted_date = df.predecessor_delisted_date.astype(str)

    json_file = os.path.join(d, 'share_transformation.json')
    with open(json_file, 'w') as f:
        f.write(df.to_json(orient='index'))


def init_future_info(d):
    all_futures_info = []
    underlying_symbol_list = []
    fields = ['close_commission_ratio', 'close_commission_today_ratio', 'commission_type', 'open_commission_ratio']

    futures_order_book_id = rqdatac.all_instruments(type='Future')['order_book_id'].unique()
    for future in futures_order_book_id:
        future_dict = {}
        underlying_symbol = re.match(r'^[a-zA-Z]*', future).group()
        commission = rqdatac.futures.get_commission_margin(future)
        if not commission.empty:
            future_dict['order_book_id'] = future
            commission = commission.iloc[0]
            for p in fields:
                future_dict[p] = commission[p]
            future_dict['tick_size'] = rqdatac.instruments(future).tick_size()
        elif underlying_symbol not in underlying_symbol_list:
            if underlying_symbol in {'S', 'TC', 'ER', 'WS', 'WT', 'RO', 'ME'}:
                continue
            underlying_symbol_list.append(underlying_symbol)
            future_dict['underlying_symbol'] = underlying_symbol
            try:
                dominant = rqdatac.futures.get_dominant(underlying_symbol).iloc[-1]
            except AttributeError:
                # FIXME: why get_dominant return None???
                continue
            commission = rqdatac.futures.get_commission_margin(dominant).iloc[0]
            for p in fields:
                future_dict[p] = commission[p]
            future_dict['tick_size'] = rqdatac.instruments(dominant).tick_size()
        else:
            continue
        all_futures_info.append(future_dict)

    hard_info = [{'underlying_symbol': 'TC',
                  'close_commission_ratio': 4.0,
                  'close_commission_today_ratio': 0.0,
                  'commission_type': "by_volume",
                  'open_commission_ratio': 4.0,
                  'tick_size': 0.2},
                 {'underlying_symbol': 'ER',
                  'close_commission_ratio': 2.5,
                  'close_commission_today_ratio': 2.5,
                  'commission_type': "by_volume",
                  'open_commission_ratio': 2.5,
                  'tick_size': 1.0},
                 {'underlying_symbol': 'WS',
                  'close_commission_ratio': 2.5,
                  'close_commission_today_ratio': 0.0,
                  'commission_type': "by_volume",
                  'open_commission_ratio': 2.5,
                  'tick_size': 1.0},
                 {'underlying_symbol': 'RO',
                  'close_commission_ratio': 2.5,
                  'close_commission_today_ratio': 0.0,
                  'commission_type': "by_volume",
                  'open_commission_ratio': 2.5,
                  'tick_size': 2.0},
                 {'underlying_symbol': 'ME',
                  'close_commission_ratio': 1.4,
                  'close_commission_today_ratio': 0.0,
                  'commission_type': "by_volume",
                  'open_commission_ratio': 1.4,
                  'tick_size': 1.0}]

    all_futures_info += hard_info

    with open(os.path.join(d, 'future_info.json'), 'w') as f:
        json.dump(all_futures_info, f, separators=(',', ':'), indent=2)


def gen_future_info(d):
    future_info_file = os.path.join(d, 'future_info.json')
    if not os.path.exists(future_info_file):
        init_future_info(d)
        return

    with open(future_info_file, 'r') as f:
        all_futures_info = json.load(f)

    future_list = []
    symbol_list = []
    param = ['close_commission_ratio', 'close_commission_today_ratio', 'commission_type', 'open_commission_ratio']

    for i in all_futures_info:
        if i.get('order_book_id'):
            future_list.append(i.get('order_book_id'))
        else:
            symbol_list.append(i.get('underlying_symbol'))

    futures_order_book_id = rqdatac.all_instruments(type='Future')['order_book_id'].unique()
    for future in futures_order_book_id:
        underlying_symbol = re.match(r'^[a-zA-Z]*', future).group()
        if future in future_list:
            continue
        future_dict = {}
        commission = rqdatac.futures.get_commission_margin(future)
        if not commission.empty:
            future_list.append(future)
            future_dict['order_book_id'] = future
            commission = commission.iloc[0]
            for p in param:
                future_dict[p] = commission[p]
            future_dict['tick_size'] = rqdatac.instruments(future).tick_size()
        elif underlying_symbol in symbol_list \
                or underlying_symbol in {'S', 'TC', 'ER', 'WS', 'WT', 'RO', 'ME'}:
            continue
        else:
            symbol_list.append(underlying_symbol)
            future_dict['underlying_symbol'] = underlying_symbol
            try:
                dominant = rqdatac.futures.get_dominant(underlying_symbol).iloc[-1]
            except AttributeError:
                # FIXME: why get_dominant return None???
                continue
            commission = rqdatac.futures.get_commission_margin(dominant).iloc[0]

            for p in param:
                future_dict[p] = commission[p]
            future_dict['tick_size'] = rqdatac.instruments(dominant).tick_size()
        all_futures_info.append(future_dict)

    with open(os.path.join(d, 'future_info.json'), 'w') as f:
        json.dump(all_futures_info, f, separators=(',', ':'), indent=2)


class GenerateFileTask(ProgressedTask):
    def __init__(self, func):
        self._func = func
        self._step = 100

    @property
    def total_steps(self):
        # type: () -> int
        return self._step

    def __call__(self, *args, **kwargs):
        self._func(*args, **kwargs)
        yield self._step


STOCK_FIELDS = ['open', 'close', 'high', 'low', 'limit_up', 'limit_down', 'volume', 'total_turnover']
INDEX_FIELDS = ['open', 'close', 'high', 'low', 'volume', 'total_turnover']
FUTURES_FIELDS = STOCK_FIELDS + ['settlement', 'prev_settlement', 'open_interest']
FUND_FIELDS = STOCK_FIELDS


class DayBarTask(ProgressedTask):
    def __init__(self, order_book_ids):
        self._order_book_ids = order_book_ids

    @property
    def total_steps(self):
        # type: () -> int
        return len(self._order_book_ids)

    def __call__(self, path, fields, **kwargs):
        raise NotImplementedError


class GenerateDayBarTask(DayBarTask):
    def __call__(self, path, fields, **kwargs):
        with h5py.File(path, 'w') as h5:
            i, step = 0, 300
            while True:
                order_book_ids = self._order_book_ids[i:i + step]
                df = rqdatac.get_price(order_book_ids, START_DATE, datetime.date.today(), '1d',
                                       adjust_type='none', fields=fields, expect_df=True)
                if not (df is None or df.empty):
                    df.reset_index(inplace=True)
                    df['datetime'] = [convert_date_to_int(d) for d in df['date']]
                    del df['date']
                    df.set_index(['order_book_id', 'datetime'], inplace=True)
                    df.sort_index(inplace=True)
                    for order_book_id in df.index.levels[0]:
                        h5.create_dataset(order_book_id, data=df.loc[order_book_id].to_records(), **kwargs)
                i += step
                yield len(order_book_ids)
                if i >= len(self._order_book_ids):
                    break


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

    def __call__(self, path, fields, **kwargs):
        need_recreate_h5 = False
        with h5py.File(path, 'r') as h5:
            need_recreate_h5 = not self.h5_has_valid_fields(h5, fields)
        if need_recreate_h5:
            yield from GenerateDayBarTask(self._order_book_ids)(path, fields, **kwargs)
        else:
            with h5py.File(path, 'a') as h5:
                for order_book_id in self._order_book_ids:
                    if order_book_id in h5:
                        try:
                            start_date = rqdatac.get_next_trading_date(int(h5[order_book_id]['datetime'][-1] // 1000000))
                        except ValueError:
                            h5.pop(order_book_id)
                            start_date = START_DATE
                    else:
                        start_date = START_DATE
                    df = rqdatac.get_price(order_book_id, start_date, END_DATE, '1d',
                                        adjust_type='none', fields=fields, expect_df=True)
                    if not (df is None or df.empty):
                        df = df[fields]  # Future order_book_id like SC888 will auto add 'dominant_id'
                        df = df.loc[order_book_id]
                        df.reset_index(inplace=True)
                        df['datetime'] = [convert_date_to_int(d) for d in df['date']]
                        del df['date']
                        df.set_index('datetime', inplace=True)
                        if order_book_id in h5:
                            data = np.array(
                                [tuple(i) for i in chain(h5[order_book_id][:], df.to_records())],
                                dtype=h5[order_book_id].dtype
                            )
                            del h5[order_book_id]
                            h5.create_dataset(order_book_id, data=data, **kwargs)
                        else:
                            h5.create_dataset(order_book_id, data=df.to_records(), **kwargs)
                    yield 1


def init_rqdatac_with_warnings_catch():
    import warnings
    with warnings.catch_warnings(record=True):
        # catch warning: rqdatac is already inited. Settings will be changed
        rqdatac.init()


def update_bundle(path, create, enable_compression=False, concurrency=1):
    if create:
        _DayBarTask = GenerateDayBarTask
    else:
        _DayBarTask = UpdateDayBarTask

    kwargs = {}
    if enable_compression:
        kwargs['compression'] = 9

    day_bar_args = (
        ("stocks.h5", rqdatac.all_instruments('CS').order_book_id.tolist(), STOCK_FIELDS),
        ("indexes.h5", rqdatac.all_instruments('INDX').order_book_id.tolist(), INDEX_FIELDS),
        ("futures.h5", rqdatac.all_instruments('Future').order_book_id.tolist(), FUTURES_FIELDS),
        ("funds.h5", rqdatac.all_instruments('FUND').order_book_id.tolist(), FUND_FIELDS),
    )

    rqdatac.reset()

    gen_file_funcs = (
        gen_instruments, gen_trading_dates, gen_dividends, gen_splits, gen_ex_factor, gen_st_days,
        gen_suspended_days, gen_yield_curve, gen_share_transformation, gen_future_info
    )

    with ProgressedProcessPoolExecutor(
            max_workers=concurrency, initializer=init_rqdatac_with_warnings_catch
    ) as executor:
        # windows上子进程需要执行rqdatac.init, 其他os则需要执行rqdatac.reset; rqdatac.init包含了rqdatac.reset的功能
        for func in gen_file_funcs:
            executor.submit(GenerateFileTask(func), path)
        for file, order_book_id, field in day_bar_args:
            executor.submit(_DayBarTask(order_book_id), os.path.join(path, file), field, **kwargs)
