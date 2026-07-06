import os
import click
import pickle
import h5py
from collections import defaultdict
from typing import Optional

import numpy as np

from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.datetime_func import convert_date_to_date_int, to_date
from rqalpha.data.bundle.utils import START_DATE
from rqalpha.model.instrument import Instrument


DAYBAR_FILE_LIST = ["stocks.h5", "indexes.h5", "futures.h5", "funds.h5"]


def _convert_string_date_to_int(date_str: str, default: Optional[int] = None):
    # 将字符串类型的 date 转换为 int
    # 如果是传入的对象是 "0000-00-00"，则直接返回 default
    if date_str == "0000-00-00":
        return default
    return convert_date_to_date_int(to_date(date_str))


def check_daybar(data_bundle_path: str):
    # 先检查是否已经成功下载 trading_dates.npy 和 instruments.pk 文件
    base_path = os.path.join(data_bundle_path, "bundle")
    if not os.path.exists(base_path):
        click.echo(_("Directory not found: {}".format(base_path)))
        return
    if not os.path.exists(os.path.join(base_path, "trading_dates.npy")) or not os.path.exists(os.path.join(base_path, "instruments.pk")):
        click.echo(_("trading_dates.npy or instruments.pk is missing in {}. Please download the base data first.".format(base_path)))
        return

    missing_file_list = []
    for daybar_file in DAYBAR_FILE_LIST:
        if not os.path.exists(os.path.join(base_path, daybar_file)):
            missing_file_list.append(daybar_file)
    if missing_file_list:
        click.echo(_("Missing files in directory {}: {}. Please update the bundle again.".format(base_path, ",".join(missing_file_list))))  #
        return

    instruments = defaultdict(list)
    with open(os.path.join(base_path, "instruments.pk"), "rb") as f:
        for i in pickle.load(f):
            i["listed_date"] = max(_convert_string_date_to_int(i["listed_date"], START_DATE), START_DATE)
            i["de_listed_date"] = _convert_string_date_to_int(i["de_listed_date"])
            instruments[i["order_book_id"]].append(i)

    # 获取所有的 trading_dates 并转化为 array
    trading_dates = np.load(os.path.join(base_path, "trading_dates.npy"))
    def _get_trading_dates(start_date: int, end_date: int) -> np.ndarray:
        start_index = np.searchsorted(trading_dates, start_date)
        end_index = np.searchsorted(trading_dates, end_date)
        return trading_dates[start_index: end_index + 1]

    def _get_previous_trading_date(trading_date: int):
        i = np.searchsorted(trading_dates, trading_date)
        if i == 0:
            return 20041231
        return trading_dates[i - 1]

    def _get_de_listed_date(order_book_id: str):
        ins = instruments[order_book_id]
        de_listed_dates = [i["de_listed_date"] for i in ins]
        if None in de_listed_dates:
            return None
        return np.array([i["de_listed_date"] for i in ins]).max()

    def _get_expected_trading_dates(order_book_id: str, is_futures: bool):
        ins = instruments[order_book_id]
        de_listed_date = _get_de_listed_date(order_book_id)
        if de_listed_date is None:
            end_date = latest_date
        else:
            last_active_date = de_listed_date if is_futures else _get_previous_trading_date(de_listed_date)
            end_date = min(last_active_date, latest_date)

        if len(ins) == 1:
            return _get_trading_dates(ins[0]["listed_date"], end_date)
        chunks = []
        for i in ins:
            if i["de_listed_date"] is None:
                chunks.append(_get_trading_dates(i["listed_date"], end_date))
            else:
                if i["listed_date"] > end_date:
                    continue
                last_active_date = i["de_listed_date"] if is_futures else _get_previous_trading_date(i["de_listed_date"])
                chunks.append(_get_trading_dates(i["listed_date"], min(end_date, last_active_date)))
        return np.concatenate(chunks)

    # 1.检查日期唯一性和连续性
    # 2.日期字段应覆盖从上市至今/退市的所有交易日
    error_oid_dic = defaultdict(list)
    error_file_dic = {}
    for daybar in DAYBAR_FILE_LIST:
        is_futures = daybar == "futures.h5"
        h5_file = os.path.join(base_path, daybar)
        try:
            h5 = h5py.File(h5_file, "r")
        except BlockingIOError: # 文件被其他进程占用
            error_file_dic[daybar] = _("File {} is being used by another process.").format(h5_file)
            continue
        except PermissionError: # 没有权限
            error_file_dic[daybar] = _("Insufficient permissions for file {}.").format(h5_file)
            continue
        except OSError:
            error_file_dic[daybar] = _(
                "Failed to open {}. The file may be corrupted, the path may be invalid, or an underlying I/O error may have occurred."
            ).format(h5_file)
            continue

        dt_cache = {}
        latest_date = None
        with h5:
            # 需要先遍历一遍 dataset，确认文件更新到的最新日期
            for order_book_id in h5.keys():
                dataset = h5[order_book_id]
                if dataset.shape is None or dataset.size == 0:
                    error_oid_dic[daybar].append(order_book_id)
                    continue
                if dataset.dtype.fields is None or "datetime" not in dataset.dtype.fields:
                    error_oid_dic[daybar].append(order_book_id)
                    continue
                dt = (dataset["datetime"] // 1_000_000).astype(int)  # type: ignore
                dt_cache[order_book_id] = dt
                latest_date = dt[-1] if latest_date is None else max(latest_date, dt[-1])
        if not dt_cache:
            error_file_dic[daybar] = _("File {} does not contain any valid dataset").format(h5_file)
            continue
        for order_book_id in list(dt_cache):
            dt = dt_cache.pop(order_book_id)
            if order_book_id in error_oid_dic.get(daybar, ()):
                continue
            if order_book_id not in instruments:
                error_oid_dic[daybar].append(order_book_id)
                continue
            if len(dt) != len(np.unique(dt)): # 存在重复日期
                error_oid_dic[daybar].append(order_book_id)
                continue
            try:
                expected_trading_dates = _get_expected_trading_dates(order_book_id, is_futures)
            except ValueError:
                error_oid_dic[daybar].append(order_book_id)
                continue
            if is_futures and Instrument.is_future_continuous_contract(order_book_id):
                # 连续合约，行情开始日期以 dt[0] 为准
                _i = np.searchsorted(expected_trading_dates, dt[0])
                expected_trading_dates = expected_trading_dates[_i: ]
            missing_dates = expected_trading_dates[~np.isin(expected_trading_dates, dt)]
            if len(missing_dates) > 0:
                error_oid_dic[daybar].append(order_book_id)
                continue

    if not error_oid_dic and not error_file_dic:
        click.echo(_("Detection complete: daybar data quality is good!"))
        return
    issue_files = [f for f in DAYBAR_FILE_LIST if f in error_file_dic or f in error_oid_dic]
    click.echo(_("Detection complete: a total of {} files have issues. The specific files and order_book_ids as follows:").format(len(issue_files)))
    for f in issue_files:
        if f in error_file_dic:
            click.echo(error_file_dic[f])
        if f in error_oid_dic:
            order_book_ids = error_oid_dic[f]
            shortened_order_book_ids = ""
            for order_book_id in order_book_ids:
                candidate = order_book_id if not shortened_order_book_ids else "{},{}".format(
                    shortened_order_book_ids, order_book_id
                )
                if len(candidate) > 100:
                    shortened_order_book_ids = "{}...".format(shortened_order_book_ids)
                    break
                shortened_order_book_ids = candidate
            click.echo(_("{}(total of {} anomaly): {}").format(
                os.path.join(base_path, f), len(order_book_ids),
                shortened_order_book_ids
            ))
