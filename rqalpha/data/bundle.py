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
from rqalpha.utils.exception import RQDatacVersionTooLow
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import system_log, user_system_log

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
    need_cols = ["dividend_cash_before_tax", "book_closure_date", "ex_dividend_date", "payable_date", "round_lot"]
    dividend = dividend[need_cols]
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


def gen_future_info(d):
    future_info_file = os.path.join(d, 'future_info.json')

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
                    dominant = rqdatac.futures.get_dominant(future_info["underlying_symbol"])[-1]
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
        underlying_symbol = re.match(r'^[a-zA-Z]*', future).group()
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
            future_dict['margin_rate'] = instruemnts_data.margin_rate
            future_dict['tick_size'] = instruemnts_data.tick_size()
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
            commission = commission_df[commission_df['order_book_id'] == dominant].iloc[0]

            for p in param:
                future_dict[p] = commission[p]
            instruemnts_data = rqdatac.instruments(dominant)
            future_dict['margin_rate'] = instruemnts_data.margin_rate
            future_dict['tick_size'] = instruemnts_data.tick_size()
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


STOCK_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'limit_up', 'limit_down', 'volume', 'total_turnover']
INDEX_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'volume', 'total_turnover']
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
        try:
            with h5py.File(path, 'r') as h5:
                need_recreate_h5 = not self.h5_has_valid_fields(h5, fields)
        except (OSError, RuntimeError):
            need_recreate_h5 = True
        if need_recreate_h5:
            yield from GenerateDayBarTask(self._order_book_ids)(path, fields, **kwargs)
        else:
            try:
                h5 = h5py.File(path, 'a')
            except OSError:
                raise OSError("File {} update failed, if it is using, please update later, "
                              "or you can delete then update again".format(path))
            try:
                is_futures = "futures" == os.path.basename(path).split(".")[0]
                for order_book_id in self._order_book_ids:
                    # 特殊处理前复权合约，需要全量更新
                    is_pre = is_futures and "888" in order_book_id
                    if order_book_id in h5 and not is_pre:
                        try:
                            last_date = int(h5[order_book_id]['datetime'][-1] // 1000000)
                        except OSError:
                            raise OSError("File {} update failed, if it is using, please update later, "
                                          "or you can delete then update again".format(path))
                        except ValueError:
                            h5.pop(order_book_id)
                            start_date = START_DATE
                        else:
                            start_date = rqdatac.get_next_trading_date(last_date)
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
            finally:
                h5.close()


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


FUTURES_TRADING_PARAMETERS_FIELDS = ["long_margin_ratio", "short_margin_ratio", "commission_type", "open_commission", "close_commission", "close_commission_today"]
TRADING_PARAMETERS_START_DATE = 20100401
FUTURES_TRADING_PARAMETERS_FILE = "futures_trading_parameters.h5"


class FuturesTradingParametersTask(object):
    def __init__(self, order_book_ids, underlying_symbols):
        self._order_book_ids = order_book_ids
        self._underlying_symbols = underlying_symbols
    
    def __call__(self, path, fields, end_date):
        if rqdatac.__version__ < '2.11.12':
            raise RQDatacVersionTooLow(_("RQAlpha already supports backtesting using futures historical margins and rates, please upgrade RQDatac to version 2.11.12 and above to use it"))
            
        if not os.path.exists(path):
            self.generate_futures_trading_parameters(path, fields, end_date)
        else:
            self.update_futures_trading_parameters(path, fields, end_date)
    
    def generate_futures_trading_parameters(self, path, fields, end_date, recreate_futures_list=None):
        # type: (str, list, datetime.date, list) -> None
        if not recreate_futures_list:
            system_log.info(_("Futures historical trading parameters data is being updated, please wait......"))
        order_book_ids = self._order_book_ids
        if recreate_futures_list:
            order_book_ids = recreate_futures_list      
        df = rqdatac.futures.get_trading_parameters(order_book_ids, TRADING_PARAMETERS_START_DATE, end_date, fields)
        if not (df is None or df.empty):
            df.dropna(axis=0, how="all")
            df.reset_index(inplace=True)
            df['datetime'] = df['trading_date'].map(convert_date_to_date_int)
            del df["trading_date"]
            df['commission_type'] = df['commission_type'].map(self.set_commission_type)
            df.rename(columns={
                'close_commission': "close_commission_ratio",
                'close_commission_today': "close_commission_today_ratio",
                'open_commission': 'open_commission_ratio'
                }, inplace=True)
            df.set_index(["order_book_id", "datetime"], inplace=True)
            df.sort_index(inplace=True)
            with h5py.File(path, "w") as h5:
                for order_book_id in df.index.levels[0]:
                    h5.create_dataset(order_book_id, data=df.loc[order_book_id].to_records())
        # 更新期货连续合约的历史交易参数数据（当函数执行目的为补充上次未正常更新的数据时，不需要执行此段逻辑）
        if recreate_futures_list is None:
            with h5py.File(path, "a") as h5:
                df = rqdatac.all_instruments("Future")
                for underlying_symbol in self._underlying_symbols:
                    futures_continuous_contract = df[(df['underlying_symbol'] == underlying_symbol) & (df["listed_date"] == '0000-00-00')].order_book_id.tolist()
                    s = rqdatac.futures.get_dominant(underlying_symbol, TRADING_PARAMETERS_START_DATE, end_date)
                    if (s is None or s.empty):
                        continue
                    s = s.to_frame().reset_index()
                    s['date'] = s['date'].map(convert_date_to_date_int)
                    s.set_index(['date'], inplace=True)
                    trading_parameters_list = []
                    for date in s.index:
                        try:
                            data = h5[s['dominant'][date]][:]
                        except KeyError:
                            continue
                        trading_parameters = data[data['datetime'] == date]
                        if len(trading_parameters) != 0:
                            trading_parameters_list.append(trading_parameters[0])
                    data = np.array(trading_parameters_list)
                    for order_book_id in futures_continuous_contract:
                        h5.create_dataset(order_book_id, data=data)

    def update_futures_trading_parameters(self, path, fields, end_date):
        # type: (str, list, datetime.date) -> None
        try:
            h5 = h5py.File(path, "a")
            h5.close()
        except OSError as e:
            raise OSError(_("File {} update failed, if it is using, please update later, or you can delete then update again".format(path))) from e
        last_date = self.get_h5_last_date(path)
        recreate_futures_list = self.get_recreate_futures_list(path, last_date)
        if recreate_futures_list:
            self.generate_futures_trading_parameters(path, fields, last_date, recreate_futures_list=recreate_futures_list)
        if end_date > last_date:
            system_log.info(_("Futures historical trading parameters data is being updated, please wait......"))
            if rqdatac.get_previous_trading_date(end_date) == last_date:
                return
            else:
                start_date = rqdatac.get_next_trading_date(last_date)
                df = rqdatac.futures.get_trading_parameters(self._order_book_ids, start_date, end_date, fields)
                if not(df is None or df.empty):
                    df = df.dropna(axis=0, how="all")
                    df.reset_index(inplace=True)
                    df['datetime'] = df['trading_date'].map(convert_date_to_date_int)
                    del [df['trading_date']]
                    df['commission_type'] = df['commission_type'].map(self.set_commission_type)
                    df.rename(columns={
                        'close_commission': "close_commission_ratio",
                        'close_commission_today': "close_commission_today_ratio",
                        'open_commission': 'open_commission_ratio'
                        }, inplace=True)
                    df.set_index(['order_book_id', 'datetime'], inplace=True)
                    with h5py.File(path, "a") as h5:
                        for order_book_id in df.index.levels[0]:
                            if order_book_id in h5:
                                data = np.array(
                                    [tuple(i) for i in chain(h5[order_book_id][:], df.loc[order_book_id].to_records())],
                                    dtype=h5[order_book_id].dtype
                                )
                                del h5[order_book_id]
                                h5.create_dataset(order_book_id, data=data)
                            else:
                                h5.create_dataset(order_book_id, data=df.loc[order_book_id].to_records())
                # 更新期货连续合约历史交易参数
                with h5py.File(path, "a") as h5:
                    df = rqdatac.all_instruments("Future")
                    for underlying_symbol in self._underlying_symbols:
                        futures_continuous_contract = df[(df['underlying_symbol'] == underlying_symbol) & (df["listed_date"] == '0000-00-00')].order_book_id.tolist()
                        s = rqdatac.futures.get_dominant(underlying_symbol, start_date, end_date)
                        if (s is None or s.empty):
                            continue
                        s = s.to_frame().reset_index()
                        s['date'] = s['date'].map(convert_date_to_date_int)
                        s.set_index(['date'], inplace=True)
                        trading_parameters_list = []
                        for date in s.index:
                            try:
                                data = h5[s['dominant'][date]][:]
                            except KeyError:
                                continue
                            trading_parameters = data[data['datetime'] == date]
                            if len(trading_parameters) != 0:
                                trading_parameters_list.append(trading_parameters[0])
                        for order_book_id in futures_continuous_contract:
                            if order_book_id in h5:
                                data = np.array(
                                    [tuple(i) for i in chain(h5[order_book_id][:], trading_parameters_list)],
                                    dtype=h5[order_book_id].dtype
                                )
                                del h5[order_book_id]
                                h5.create_dataset(order_book_id, data=data)
                            else:
                                h5.create_dataset(order_book_id, data=np.array(trading_parameters))

    def set_commission_type(self, commission_type):
        if commission_type == "by_money":
            commission_type = 0
        elif commission_type == "by_volume":
            commission_type = 1
        return commission_type
    
    def get_h5_last_date(self, path):
        last_date = TRADING_PARAMETERS_START_DATE
        with h5py.File(path, "r") as h5:
            for key in h5.keys():
                if int(h5[key]['datetime'][-1]) > last_date:
                    last_date = h5[key]['datetime'][-1]
        last_date = datetime.datetime.strptime(str(last_date), "%Y%m%d").date()
        return last_date

    def get_recreate_futures_list(self, path, h5_last_date):
        # type: (str, datetime.date) -> list
        """
        用户在运行策略的过程中可能中断进程，进而可能导致在创建 h5 文件时，部分合约没有成功 download
        通过该函数，获取在上一次更新中因为异常而没有更新的合约
        """
        recreate_futures_list = []
        df = rqdatac.all_instruments("Future")
        last_update_futures_list = df[(df['de_listed_date'] >= str(TRADING_PARAMETERS_START_DATE)) & (df['listed_date'] <= h5_last_date.strftime("%Y%m%d"))].order_book_id.to_list()
        with h5py.File(path, "r") as h5:
            h5_order_book_ids = h5.keys()
            for order_book_id in last_update_futures_list:
                if order_book_id in h5_order_book_ids:
                    continue
                else:
                    recreate_futures_list.append(order_book_id)
        return recreate_futures_list


def update_futures_trading_parameters(path, end_date):
    # type: (str, datetime.date) -> None
    df = rqdatac.all_instruments("Future")
    order_book_ids = (df[df['de_listed_date'] >= str(TRADING_PARAMETERS_START_DATE)]).order_book_id.tolist()
    underlying_symbols = list(set((df[df['de_listed_date'] >= str(TRADING_PARAMETERS_START_DATE)]).underlying_symbol.tolist()))
    FuturesTradingParametersTask(order_book_ids, underlying_symbols)(
        os.path.join(path, FUTURES_TRADING_PARAMETERS_FILE), 
        FUTURES_TRADING_PARAMETERS_FIELDS, 
        end_date
    )
