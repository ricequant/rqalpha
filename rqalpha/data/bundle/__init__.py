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
import uuid
from typing import Optional, List, Iterable, Tuple
import multiprocessing
from multiprocessing.sharedctypes import Synchronized
from ctypes import c_bool
from time import sleep

import h5py
import numpy as np
import pandas as pd
from rqalpha.apis.api_rqdatac import rqdatac
from rqalpha.utils.concurrent import ProgressedProcessPoolExecutor, ProgressedTask
from rqalpha.utils.datetime_func import convert_date_to_date_int, convert_date_to_int
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import init_logger, system_log
from rqalpha.data.bundle.utils import (
    set_sval, sval, bind_error_list, reset_error_list, log_and_mark_error, START_DATE, END_DATE,
    STOCK_FIELDS, FUTURES_FIELDS, INDEX_FIELDS, FUND_FIELDS
)
from rqalpha.data.bundle.daybar import GenerateDayBarTask, UpdateDayBarTask

from rqalpha.data.bundle.automatic_update import AutomaticUpdateBundle


CORPORATE_ACTION_EXCLUSIONS = ["Future", "Option", "Spot"]
INSTRUMENTS_RETRY_COUNT = 5


def _get_oids_with_corporate_action_exclusions():
    ints = rqdatac.all_instruments()
    ints = ints[~ints.type.isin(CORPORATE_ACTION_EXCLUSIONS)]
    return ints.order_book_id.tolist()


def write_instruments(data_bundle_path: str, instruments: Iterable, file_name: str = "instruments.pk"):
    """
    将已获取的 rqdatac Instrument 对象序列化后写入指定 bundle 目录，供本地数据源加载使用。

    :param data_bundle_path: bundle 目录路径
    :param instruments: 待写入 bundle 的 rqdatac Instrument 对象集合
    :param file_name: instruments bundle 文件名
    """
    if not instruments:  # 预防传入空列表
        raise RuntimeError(_("Invalid instruments list!"))
    instruments = [i.__dict__ for i in instruments]
    pkl_path = os.path.join(data_bundle_path, file_name)
    tmp_dir = os.path.dirname(pkl_path) or os.curdir
    tmp_file_prefix = "{}.tmp.".format(os.path.basename(pkl_path))
    for tmp_file_name in os.listdir(tmp_dir):
        tmp_path = os.path.join(tmp_dir, tmp_file_name)
        if (
            tmp_file_name.startswith(tmp_file_prefix)
            and os.path.getmtime(tmp_path) <= (datetime.datetime.now() - datetime.timedelta(days=1)).timestamp()
        ):
            os.remove(tmp_path)

    tmp_file_name = "{}.tmp.{}".format(file_name, uuid.uuid4().hex)
    tmp_path = os.path.join(data_bundle_path, tmp_file_name)
    try:
        with open(tmp_path, "wb") as out:
            pickle.dump(instruments, out, protocol=2)
        i = 0
        while True:
            try:
                os.replace(tmp_path, pkl_path)
                break
            except PermissionError as e:
                # 可能存在多进程同时执行，replace 时有其他进程正在读取目标文件的情况
                if i < INSTRUMENTS_RETRY_COUNT:
                    sleep(0.1)
                    i += 1
                else:
                    raise e
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def gen_instruments(data_bundle_path: str):
    order_book_ids = []
    for instrument_type in ["CS", "ETF", "LOF", "INDX", "Future", "Repo", "REITs", "FUND"]:
        order_book_ids.extend(rqdatac.all_instruments(instrument_type).order_book_id.tolist())
    order_book_ids = list(set(order_book_ids))
    instruments = rqdatac.instruments(order_book_ids)
    if instruments is None:
        raise RuntimeError(_("Got instruments failed!"))
    write_instruments(data_bundle_path, instruments)


def gen_yield_curve(data_bundle_path: str):
    yield_curve: Optional[pd.DataFrame] = rqdatac.get_yield_curve(start_date=START_DATE, end_date=datetime.date.today())
    if yield_curve is None or yield_curve.empty:
        raise RuntimeError(_("Get yield curve data error."))
    yield_curve.index = [convert_date_to_date_int(d) for d in yield_curve.index]
    yield_curve.index.name = 'date'
    with h5py.File(os.path.join(data_bundle_path, 'yield_curve.h5'), 'w') as f:
        f.create_dataset('data', data=yield_curve.to_records())


def gen_trading_dates(data_bundle_path: str):
    dates = rqdatac.get_trading_dates(start_date=START_DATE, end_date='2999-01-01')
    dates = np.array([convert_date_to_date_int(d) for d in dates])
    np.save(os.path.join(data_bundle_path, 'trading_dates.npy'), dates, allow_pickle=False)


def gen_st_days(data_bundle_path: str):
    from rqdatac.client import get_client
    stocks = rqdatac.all_instruments('CS').order_book_id.tolist()
    st_days = get_client().execute('get_st_days', stocks, START_DATE,
                                   convert_date_to_date_int(datetime.date.today()))
    with h5py.File(os.path.join(data_bundle_path, 'st_stock_days.h5'), 'w') as h5:
        for order_book_id, days in st_days.items():
            h5[order_book_id] = days


def gen_suspended_days(data_bundle_path: str):
    from rqdatac.client import get_client
    stocks = rqdatac.all_instruments('CS').order_book_id.tolist()
    suspended_days = get_client().execute('get_suspended_days', stocks, START_DATE,
                                          convert_date_to_date_int(datetime.date.today()))
    with h5py.File(os.path.join(data_bundle_path, 'suspended_days.h5'), 'w') as h5:
        for order_book_id, days in suspended_days.items():
            h5[order_book_id] = days


class GenerateDividendBundle:
    def __init__(self, data_bundle_path: str):
        self.data_bundle_path = data_bundle_path

    def _get_dividend(self):
        order_book_ids = _get_oids_with_corporate_action_exclusions()
        return rqdatac.get_dividend(order_book_ids)

    def _write(self, data_iter: Iterable[Tuple[str, np.ndarray]]):
        with h5py.File(os.path.join(self.data_bundle_path, 'dividends.h5'), "w") as h5:
            for order_book_id, data in data_iter:
                h5.create_dataset(order_book_id, data=data)

    def __call__(self):
        dividend = self._get_dividend()
        if dividend is None:
            raise RuntimeError(_("Got no dividend data"))
        need_cols = ["dividend_cash_before_tax", "book_closure_date", "ex_dividend_date", "payable_date", "round_lot"]
        dividend = dividend[need_cols]
        dividend.reset_index(inplace=True)
        dividend.rename(columns={'declaration_announcement_date': 'announcement_date'}, inplace=True)
        for f in ('book_closure_date', 'ex_dividend_date', 'payable_date', 'announcement_date'):
            dividend[f] = [convert_date_to_date_int(d) for d in dividend[f]]
        dividend.set_index(['order_book_id', 'book_closure_date'], inplace=True)
        self._write([(
            order_book_id, dividend.loc[order_book_id].to_records()
        ) for order_book_id in dividend.index.levels[0]])  # type: ignore


class GenerateSplitBundle:
    def __init__(self, data_bundle_path: str):
        self.data_bundle_path = data_bundle_path

    def _get_split(self):
        order_book_ids = _get_oids_with_corporate_action_exclusions()
        return rqdatac.get_split(order_book_ids)

    def _write(self, data_iter: Iterable[Tuple[str, np.ndarray]]):
        with h5py.File(os.path.join(self.data_bundle_path, 'split_factor.h5'), "w") as h5:
            for order_book_id, data in data_iter:
                h5.create_dataset(order_book_id, data=data)

    def __call__(self):
        split = self._get_split()
        if split is None:
            raise RuntimeError(_("Got no split data"))
        split['split_factor'] = split['split_coefficient_to'] / split['split_coefficient_from']
        split = split[['split_factor', 'split_coefficient_to', 'split_coefficient_from']]
        split.reset_index(inplace=True)
        split.rename(columns={'ex_dividend_date': 'ex_date'}, inplace=True)  # type: ignore
        split['ex_date'] = [convert_date_to_int(d) for d in split['ex_date']]
        split.set_index(['order_book_id', 'ex_date'], inplace=True)
        self._write([(
            order_book_id, split.loc[order_book_id].to_records()
        ) for order_book_id in split.index.levels[0]])  # type: ignore


class GenerateExFactorBundle:
    def __init__(self, data_bundle_path: str):
        self.data_bundle_path = data_bundle_path

    def _get_ex_factor(self):
        order_book_ids = _get_oids_with_corporate_action_exclusions()
        return rqdatac.get_ex_factor(order_book_ids)

    def _write(self, data_iter: Iterable[Tuple[str, np.ndarray]]):
        with h5py.File(os.path.join(self.data_bundle_path, 'ex_cum_factor.h5'), "w") as h5:
            for order_book_id, data in data_iter:
                h5.create_dataset(order_book_id, data=data)

    def __call__(self):
        ex_factor = self._get_ex_factor()
        if ex_factor is None:
            raise RuntimeError(_("Got no ex factor data"))
        ex_factor.reset_index(inplace=True)
        ex_factor['ex_date'] = [convert_date_to_int(d) for d in ex_factor['ex_date']]
        ex_factor.rename(columns={'ex_date': 'start_date'}, inplace=True)
        ex_factor.set_index(['order_book_id', 'start_date'], inplace=True)
        ex_factor = ex_factor[['ex_cum_factor']]

        dtype = ex_factor.loc[ex_factor.index.levels[0][0]].to_records().dtype  # type: ignore
        initial = np.empty((1,), dtype=dtype)
        initial['start_date'] = 0
        initial['ex_cum_factor'] = 1.0

        self._write(((
            order_book_id, np.concatenate([initial, ex_factor.loc[order_book_id].to_records()])
        ) for order_book_id in ex_factor.index.levels[0]))  # type: ignore


def gen_share_transformation(data_bundle_path: str):
    df = rqdatac.get_share_transformation()
    if df is None:
        raise RuntimeError(_("Got no share transformation data"))
    df.drop_duplicates("predecessor", inplace=True)
    df.set_index('predecessor', inplace=True)
    df["effective_date"] = df.effective_date.astype(str)
    df["predecessor_delisted_date"] = df.predecessor_delisted_date.astype(str)

    json_file = os.path.join(data_bundle_path, 'share_transformation.json')
    with open(json_file, 'w') as f:
        f.write(df.to_json(orient='index'))


def gen_future_info(data_bundle_path: str):
    future_info_file = os.path.join(data_bundle_path, 'future_info.json')

    def _need_to_recreate():
        if not os.path.exists(future_info_file):
            return
        else:
            with open(future_info_file, "r") as f:
                all_futures_info = json.load(f)
                if "margin_rate" not in all_futures_info[0]:
                    return True

    def update_margin_rate(file):
        all_instruments_data = rqdatac.all_instruments("Future")
        with open(file, "r") as f:
            all_futures_info = json.load(f)
            new_all_futures_info = []
            for future_info in all_futures_info:
                if "order_book_id" in future_info:
                    future_info["margin_rate"] = all_instruments_data[all_instruments_data["order_book_id"] == future_info["order_book_id"]].iloc[0].margin_rate
                elif "underlying_symbol" in future_info:
                    dominant = rqdatac.futures.get_dominant(future_info["underlying_symbol"])[-1]  # type: ignore
                    future_info["margin_rate"] = all_instruments_data[all_instruments_data["order_book_id"] == dominant].iloc[0].margin_rate
                new_all_futures_info.append(future_info)
        os.remove(file)
        with open(file, "w") as f:
            json.dump(new_all_futures_info, f, separators=(',', ':'), indent=2)

    if (_need_to_recreate()): update_margin_rate(future_info_file)

    # 新增 hard_code 的种类时，需要同时修改rqalpha.data.base_data_source.storages.FutureInfoStore.data_compatible中的内容
    hard_code = [
        {'underlying_symbol': 'TC',
          'close_commission_ratio': 4.0,
          'close_commission_today_ratio': 0.0,
          'commission_type': "by_volume",
          'open_commission_ratio': 4.0,
          'margin_rate': 0.05,
          'tick_size': 0.2},
         {'underlying_symbol': 'ER',
          'close_commission_ratio': 2.5,
          'close_commission_today_ratio': 2.5,
          'commission_type': "by_volume",
          'open_commission_ratio': 2.5,
          'margin_rate': 0.05,
          'tick_size': 1.0},
         {'underlying_symbol': 'WS',
          'close_commission_ratio': 2.5,
          'close_commission_today_ratio': 0.0,
          'commission_type': "by_volume",
          'open_commission_ratio': 2.5,
          'margin_rate': 0.05,
          'tick_size': 1.0},
         {'underlying_symbol': 'RO',
          'close_commission_ratio': 2.5,
          'close_commission_today_ratio': 0.0,
          'commission_type': "by_volume",
          'open_commission_ratio': 2.5,
          'margin_rate': 0.05,
          'tick_size': 2.0},
         {'underlying_symbol': 'ME',
          'close_commission_ratio': 1.4,
          'close_commission_today_ratio': 0.0,
          'commission_type': "by_volume",
          'open_commission_ratio': 1.4,
          'margin_rate': 0.06,
          'tick_size': 1.0},
        {'underlying_symbol': 'WT',
         'close_commission_ratio': 5.0,
         'close_commission_today_ratio': 5.0,
         'commission_type': "by_volume",
         'open_commission_ratio': 5.0,
         'margin_rate': 0.05,
         'tick_size': 1.0},
    ]

    if not os.path.exists(future_info_file):
        all_futures_info = hard_code
    else:
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

    # 当修改了hard_code以后，避免用户需要手动删除future_info.json文件
    for info in hard_code:
        if info["underlying_symbol"] not in symbol_list:
            all_futures_info.append(info)
            symbol_list.append(info["underlying_symbol"])

    futures_order_book_id = rqdatac.all_instruments(type='Future')['order_book_id'].unique()
    commission_df = rqdatac.futures.get_commission_margin()
    for future in futures_order_book_id:
        underlying_symbol_match = re.match(r'^[a-zA-Z]*', future)
        if underlying_symbol_match is None:
            system_log.error(f"Invalid future order_book_id: {future}")
        else:
            underlying_symbol = underlying_symbol_match.group()
        if future in future_list:
            continue
        future_dict = {}
        commission = commission_df[commission_df['order_book_id'] == future]
        if not commission.empty:
            future_dict['order_book_id'] = future
            commission = commission.iloc[0]
            for p in param:
                future_dict[p] = commission[p]
            instruemnts_data = rqdatac.instruments(future)
            future_dict['margin_rate'] = instruemnts_data.margin_rate  # type: ignore
            future_dict['tick_size'] = instruemnts_data.tick_size()  # type: ignore
        elif underlying_symbol in symbol_list:
            continue
        else:
            symbol_list.append(underlying_symbol)
            future_dict['underlying_symbol'] = underlying_symbol
            try:
                dominant = rqdatac.futures.get_dominant(underlying_symbol).iloc[-1]
            except AttributeError:
                # FIXME: why get_dominant return None???
                continue

            dominant_indexer = commission_df["order_book_id"] == dominant
            if not dominant_indexer.any():
                # S0301：大豆期货的最后一个合约，该合约出现在 instrument 中，但取不到 commission，这种情况忽略掉
                continue
            commission = commission_df[dominant_indexer].iloc[0]

            for p in param:
                future_dict[p] = commission[p]
            instruemnts_data = rqdatac.instruments(dominant)
            future_dict['margin_rate'] = instruemnts_data.margin_rate  # type: ignore
            future_dict['tick_size'] = instruemnts_data.tick_size()  # type: ignore
        all_futures_info.append(future_dict)

    with open(future_info_file, 'w') as f:
        json.dump(all_futures_info, f, separators=(',', ':'), indent=2)


class GenerateFileTask(ProgressedTask):
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._step = 100

    @property
    def total_steps(self) -> int:
        return self._step

    def __call__(self):
        try:
            self._func(*self._args, **self._kwargs)
        except Exception as e:
            log_and_mark_error(str(e))
        yield self._step


def process_init(args: Optional[Synchronized] = None, kwargs=None, errors=None):
    kwargs = kwargs or {}
    import warnings
    with warnings.catch_warnings(record=True):
        # catch warning: rqdatac is already inited. Settings will be changed
        rqdatac.init(**kwargs)
    init_logger()
    # Initialize process shared variables
    global sval
    if args:
        set_sval(args)
        sval = args
    if errors is not None:
        bind_error_list(errors)


def gather_tasks(path: str, create: bool, enable_compression: bool, **h5_kwargs) -> List[ProgressedTask]:
    tasks = []
    if create:
        _DayBarTask = GenerateDayBarTask
    else:
        _DayBarTask = UpdateDayBarTask

    init_logger()
    day_bar_args = (
        ("stocks.h5", rqdatac.all_instruments('CS').order_book_id.tolist(), STOCK_FIELDS),
        ("indexes.h5", rqdatac.all_instruments('INDX').order_book_id.tolist(), INDEX_FIELDS),
        ("futures.h5", rqdatac.all_instruments('Future').order_book_id.tolist(), FUTURES_FIELDS),
        ("funds.h5", rqdatac.all_instruments('FUND').order_book_id.tolist(), FUND_FIELDS),
    )

    gen_file_funcs = (
        gen_instruments, gen_trading_dates, gen_st_days,
        gen_suspended_days, gen_yield_curve, gen_share_transformation, gen_future_info
    )
    if enable_compression:
        h5_kwargs['compression'] = 9
    # windows上子进程需要执行rqdatac.init, 其他os则需要执行rqdatac.reset; rqdatac.init包含了rqdatac.reset的功能
    for file, order_book_id, field in day_bar_args:
        tasks.append(_DayBarTask(order_book_id, os.path.join(path, file), field, **h5_kwargs))
    for func in gen_file_funcs:
        tasks.append(GenerateFileTask(func, path))
    tasks.append(GenerateFileTask(GenerateDividendBundle(path)))
    tasks.append(GenerateFileTask(GenerateSplitBundle(path)))
    tasks.append(GenerateFileTask(GenerateExFactorBundle(path)))
    return tasks


def run_tasks(tasks: List[ProgressedTask], concurrency: int = 1, **rqdatac_kwargs):
    succeed = multiprocessing.Value(c_bool, True)
    errors = reset_error_list()
    with ProgressedProcessPoolExecutor(
            max_workers=concurrency, initializer=process_init,
            initargs=(succeed, rqdatac_kwargs, errors)
    ) as executor:
        for task in tasks:
            executor.submit(task)
    return succeed.value


def update_bundle(path, create, enable_compression=False, concurrency=1, rqdata_kwargs=None, **h5_kwargs):
    tasks = gather_tasks(path, create, enable_compression, **h5_kwargs)
    rqdata_kwargs = rqdata_kwargs or {}
    return run_tasks(tasks, concurrency, **rqdata_kwargs)
