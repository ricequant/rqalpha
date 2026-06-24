import os
import click
import pickle
import h5py
from collections import defaultdict
import datetime

import numpy as np
import pandas as pd

from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.datetime_func import convert_date_to_date_int


DAYBAR_FILE_LIST = ["stocks.h5", "indexes.h5", "futures.h5", "funds.h5"]


def check_daybar(data_bundle_path: str):
    # 先检查是否已经成功下载 trading_dates.npy 和 instruments.pk 文件
    base_path = os.path.join(data_bundle_path, "bundle")
    if not os.path.exists(base_path):
        click.echo(_("Directory not found: {}".format(base_path)))  # 未找到文件目录：{}
        return
    if not os.path.exists(os.path.join(base_path, "trading_dates.npy")) or not os.path.exists(os.path.join(base_path, "instruments.pk")):
        click.echo(_("trading_dates.npy or instruments.pk is missing in {}. Please download the base data first.".format(base_path)))  # 当前目录缺少 trading_dates.npy 或 instruments.pk 文件，请先下载 base 数据
        return
    
    missing_file_list = []
    for daybar_file in DAYBAR_FILE_LIST:
        if not os.path.exists(os.path.join(base_path, daybar_file)):
            missing_file_list.append(daybar_file)
    if missing_file_list:
        click.echo(_("Missing files in directory {}: {}. Please update the bundle again.".format(base_path, ",".join(missing_file_list))))  # 
        return
    
    instruments = {}
    with open(os.path.join(base_path, "instruments.pk"), "rb") as f:
        for i in pickle.load(f):
            instruments[i["order_book_id"]] = i
    
    # 获取所有的 trading_dates 并转化为 array
    trading_dates = np.load(os.path.join(base_path, "trading_dates.npy"))
    def _get_trading_dates(start_date, end_date):
        start_index = np.searchsorted(trading_dates, start_date)
        end_index = np.searchsorted(trading_dates, end_date)
        return trading_dates[start_index: end_index + 1]
    
    def _get_previous_trading_date(trading_date):
        i = np.searchsorted(trading_dates, trading_date)
        if i == 0:
            return 20041231
        return trading_dates[i - 1]

    # 1.检查日期唯一性和连续性 
    # 2.日期字段应覆盖从上市至今/退市的所有交易日
    error_oid_dic = defaultdict(list)
    for daybar in DAYBAR_FILE_LIST:
        oids_latest_dt_dic = {}  # 用于记录未退市合约的最新日期数据
        h5_file = os.path.join(base_path, daybar)
        try:
            with h5py.File(h5_file, "r") as h5:
                for order_book_id in h5.keys():
                    dt = h5[order_book_id]["datetime"] / 1e6  # type: ignore
                    if len(dt) != len(np.unique(dt)): # 存在重复日期
                        error_oid_dic[daybar].append(order_book_id)
                        continue
                    expected_trading_dates = _get_trading_dates(dt[0], dt[-1])
                    missing_dates = expected_trading_dates[~np.isin(expected_trading_dates, dt)]
                    if len(missing_dates) > 0:
                        error_oid_dic[daybar].append(order_book_id)
                    ins = instruments[order_book_id]
                    if ins["de_listed_date"] == "0000-00-00":
                        oids_latest_dt_dic[order_book_id] = dt[-1]
                    else:
                        de_listed_previous_date = _get_previous_trading_date(convert_date_to_date_int(datetime.datetime.strptime(ins["de_listed_date"], "%Y-%m-%d")))
                        if de_listed_previous_date > dt[-1]:
                            error_oid_dic[daybar].append(order_book_id)
        except BlockingIOError: # 文件被其他进程占用
            click.echo(_("File {} is being used by another process.".format(h5_file)))  # 文件 {} 被其他进程占用
        except PermissionError: # 没有权限
            click.echo(_("Insufficient prmissions for file {}.".format(h5_file)))  # 缺少文件 {} 的权限
        except OSError:
            click.echo(_("Failed to open {}. The file may be corrupted, the path may be invalid, or an underlying I/O error may have occurred."))  # {}无法正常打开,可能是文件损坏,路径异常或底层I/O错误
        
        oids_latest_dt = pd.Series(oids_latest_dt_dic)
        incomplete = oids_latest_dt[oids_latest_dt < oids_latest_dt.max()]
        if not incomplete.empty:
            error_oid_dic[daybar].extend(incomplete.index.tolist())
