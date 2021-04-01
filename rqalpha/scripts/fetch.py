#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-17 19:54
"""
import datetime
import time
from typing import List, Tuple, Union

import pandas as pd
import pymongo
import tushare as ts



REPORT_DATE_TAILS = ["0331", "0630", "0930", "1231"]
SHEET_TYPE = ["income", "balancesheet", "cashflow"]
REPORT_TYPE = ['1', '2', '3', '4', '5', '11']


def QA_fetch_get_individual_financial(
        code: str,
        start: Union[str, datetime.datetime, pd.Timestamp] = None,
        end: Union[str, datetime.datetime, pd.Timestamp] = None,
        report_date: Union[str, datetime.datetime] = None,
        sheet_type: str = "income",
        report_type: Union[int, str] = 1,
        fields: Union[str, Tuple, List] = None,
        wait_seconds: int = 61,
        max_trial: int = 3) -> pd.DataFrame:
    """个股财务报表网络查询接口，注意，这里的 start 与 end 是针对 report_date 进行范围查询
    Args:
        code (str): 股票代码
        start (Union[str, datetime.datetime, pd.Timestamp], optional): 查询起始时间，默认为 None
        end (Union[str, datetime.datetime, pd.Timestamp], optional): 查询结束时间，默认为 None
        report_date (Union[str, datetime.datetime], optional): 报告期. 默认为 None，如果使用了 report_date, 则 start 与 end 参数不再起作用
        sheet_type (str, optional): 报表类型，默认为 "income" 类型
            (利润表 "income"|
            资产负债表 "balancesheet"|
            现金流量表 "cashflow"|
            业绩预告 "forecast"|
            业绩快报 "express")
        report_type (Union[int, str], optional): 报告类型. 默认为 1。
            (1	合并报表	上市公司最新报表（默认）|
            2	单季合并	单一季度的合并报表 |
            3	调整单季合并表	调整后的单季合并报表（如果有） |
            4	调整合并报表	本年度公布上年同期的财务报表数据，报告期为上年度 |
            5	调整前合并报表	数据发生变更，将原数据进行保留，即调整前的原数据 |
            6	母公司报表	该公司母公司的财务报表数据 |
            7	母公司单季表	母公司的单季度表 |
            8	母公司调整单季表	母公司调整后的单季表 |
            9	母公司调整表	该公司母公司的本年度公布上年同期的财务报表数据 |
            10 母公司调整前报表	母公司调整之前的原始财务报表数据 |
            11 调整前合并报表	调整之前合并报表原数据 |
            12 母公司调整前报表	母公司报表发生变更前保留的原数据)
        fields (Union[str, Tuple, List], optional): 指定数据范围，如果设置为 None，则返回所有数据. 默认为 None.
        wait_seconds (int, optional): 等待重试时间. 默认为 61 秒.
        max_trial (int, optional): 最大重试次数. 默认为 3.
    Returns:
        pd.DataFrame: 返回指定个股时间范围内指定类型的报表数据
    """
    def _get_individual_financial(code, report_date, report_type, sheet_type, fields, wait_seconds, trial_count):
        nonlocal pro, max_trial
        if trial_count >= max_trial:
            raise ValueError("[ERROR]\tEXCEED MAX TRIAL!")
        try:
            if not fields:
                df = eval(
                    f"pro.{sheet_type}(ts_code='{code}', period='{report_date}', report_type={report_type})")
            else:
                df = eval(
                    f"pro.{sheet_type}(ts_code='{code}', period='{report_date}', report_type={report_type}, fields={fields})")
            return df.rename(columns={"ts_code": "code", "end_date": "report_date"})
        except Exception as e:
            print(e)
            time.sleep(wait_seconds)
            _get_individual_financial(
                code, report_date, report_type, sheet_type, fields, wait_seconds, trial_count+1)

    pro = get_pro()
    report_type = int(report_type)
    if (not start) and (not end) and (not report_date):
        raise ValueError(
            "[QRY_DATES ERROR]\tparam 'start', 'end' and 'report_date' should not be none at the same time!")
    if isinstance(fields, str):
        fields = sorted(list(set([fields, "ts_code", "end_date",
                                  "ann_date", "f_ann_date", "report_type", "update_flag"])))
    if report_date:
        report_date = pd.Timestamp(report_date)
        year = report_date.year
        report_date_lists = [
            pd.Timestamp(str(year) + report_date_tail) for report_date_tail in REPORT_DATE_TAILS]
        if report_date not in report_date_lists:
            raise ValueError("[REPORT_DATE ERROR]")
        if sheet_type not in ["income", "balancesheet", "cashflow", "forecast", "express"]:
            raise ValueError("[SHEET_TYPE ERROR]")
        if report_type not in range(1, 13):
            raise ValueError("[REPORT_TYPE ERROR]")
        report_dates = [report_date]
    else:
        start = pd.Timestamp(start)
        start_year = start.year
        end = pd.Timestamp(end)
        end_year = end.year
        origin_year_ranges = pd.date_range(
            str(start_year), str(end_year+1), freq='Y').map(str).str.slice(0, 4).tolist()
        origin_report_ranges = pd.Series([
            pd.Timestamp(year + report_date_tail) for year in origin_year_ranges for report_date_tail in REPORT_DATE_TAILS])
        report_dates = origin_report_ranges.loc[(
            origin_report_ranges >= start) & (origin_report_ranges <= end)]
    df = pd.DataFrame()
    for report_date in report_dates:
        df = df.append(_get_individual_financial(
            code=QA_fmt_code(code, "ts"),
            report_date=report_date.strftime("%Y%m%d"),
            report_type=report_type,
            sheet_type=sheet_type,
            fields=fields,
            wait_seconds=wait_seconds,
            trial_count=0))
    df.code = QA_fmt_code_list(df.code)
    return df.reset_index(drop=True)