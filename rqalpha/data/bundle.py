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
FUTURES_TRADING_PARAMETERS_FIELDS = ["long_margin_ratio", "short_margin_ratio", "commission_type", "open_commission", "close_commission", "close_commission_today"]
TRADING_PARAMETERS_START_DATE = 20100401


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


class FuturesTradingParametersTask(ProgressedTask):
    def __init__(self, order_book_ids):
        self._order_book_ids = order_book_ids

    @property
    def total_steps(self):
        # type: () -> int
        return len(self._order_book_ids)
    
    def change_commission_type(self, commission_type):
        if commission_type == "by_money":
            commission_type = 0
        elif commission_type == "by_volume":
            commission_type = 1
        return commission_type
    
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class GeneratorFuturesTradingParametersTask(FuturesTradingParametersTask):
    def __call__(self, path, fields, end_date):
        with h5py.File(path, "w") as h5:
            df = rqdatac.futures.get_trading_parameters(self._order_book_ids, TRADING_PARAMETERS_START_DATE, end_date, fields)
            if not (df is None or df.empty):
                df.dropna(axis=0, how="all")
                df.reset_index(inplace=True)
                df.rename(columns={
                    "open_commission": "open_commission_ratio",
                    "close_commission": "close_commission_ratio",
                    "close_commission_today": "close_commission_today_ratio"
                }, inplace=True)
                df["datetime"] = [convert_date_to_int(d) for d in df["trading_date"]]
                del df["trading_date"]
                df["commission_type"] = [self.change_commission_type(v) for v in df["commission_type"]]
                df.set_index(["order_book_id", "datetime"], inplace=True)
                df.sort_index(inplace=True)
                for order_book_id in df.index.levels[0]:
                    h5.create_dataset(order_book_id, data=df.loc[order_book_id].to_records())
                

class UpdateFuturesTradingParametersTask(FuturesTradingParametersTask):
    def trading_parameters_need_to_update(self, path, end_date):
        last_date = TRADING_PARAMETERS_START_DATE * 1000000
        with h5py.File(path, "r") as h5:
            for key in h5.keys():
                if int(h5[key]['datetime'][-1]) > last_date:
                    last_date = h5[key]['datetime'][-1]
            if (last_date // 1000000) >= int(end_date):
                return False
            else:
                return last_date // 1000000
    
    def __call__(self, path, end_date, fields, **kwargs):
        need_create_h5 = False
        try:
            h5py.File(path, "r")
        except (OSError, RuntimeError):
            need_create_h5 = True
        if need_create_h5:
            GeneratorFuturesTradingParametersTask(self._order_book_ids)(path, fields, end_date, **kwargs)        
        else:
            last_date = self.trading_parameters_need_to_update(path, end_date)
            if last_date:
                try:
                    h5 = h5py.File(path, "a")
                except OSError:
                    raise OSError("File {} update failed, if it is using, please update later, "
                                  "or you can delete then update again".format(path))
                start_date = rqdatac.get_next_trading_date(str(last_date))
                df = rqdatac.futures.get_trading_parameters(self._order_book_ids, start_date, end_date, fields)
                if not(df is None or df.empty):
                    df.dropna(axis=0, how="all")
                    df.reset_index(inplace=True)
                    df['datetime'] = [convert_date_to_int(d) for d in df['trading_date']]
                    del [df['trading_date']]
                    df['commission_type'] = [self.change_commission_type(v) for v in df['commission_type']]
                    df.set_index(['order_book_id', 'datetime'], inplace=True)
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
                h5.close()


def check_rqdata_permission():
    """
    检测以下内容，均符合才会更新期货交易参数：
    1. rqdatac 版本是否为具备 futures.get_trading_parameters API 的版本
    2. 当前 rqdatac 是否具备上述 API 的使用权限
    """
    if rqdatac.__version__ < '2.11.11.4':
        from rqalpha.utils.logger import system_log
        system_log.info("RQAlpha 已支持使用期货历史保证金和费率进行回测，请将 RQDatac 升级至 2.11.12 及以上版本进行使用")
        return
    try:
        rqdatac.futures.get_trading_parameters("A1005")
    except Exception as e:
        if isinstance(e, rqdatac.share.errors.PermissionDenied):
            from rqalpha.utils.logger import system_log
            system_log.info("您的 rqdata 账号没有权限使用期货历史保证金和费率，将使用固定的保证金和费率进行回测和计算\n可联系米筐科技开通权限：0755-26569969")
            return
    return True


def update_futures_trading_parameters(path, futures_trading_parameters_config):
    update_permission = check_rqdata_permission()
    if not update_permission:
        return
    df = rqdatac.all_instruments("Future")
    order_book_ids = (df[df['de_listed_date'] >= str(TRADING_PARAMETERS_START_DATE)]).order_book_id.tolist()
    futures_trading_parameters_args = {
        "file": "futures_trading_parameters.h5",
        "order_book_ids": order_book_ids,
        "fields": FUTURES_TRADING_PARAMETERS_FIELDS
    }
    UpdateFuturesTradingParametersTask(futures_trading_parameters_args['order_book_ids'])(
        os.path.join(path, futures_trading_parameters_args['file']), 
        futures_trading_parameters_config["end_date"].strftime("%Y%m%d"), 
        futures_trading_parameters_args['fields']
        )
    return True