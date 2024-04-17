# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
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

import os
from typing import Dict, Optional
import datetime

import numpy
import pandas
from collections import ChainMap, defaultdict
from pandas import Series, DataFrame

from rqrisk import Risk
from rqrisk import WEEKLY, MONTHLY
from rqalpha.environment import Environment

from rqalpha.mod.rqalpha_mod_sys_analyser.plot.utils import max_dd as _max_dd
from rqalpha.mod.rqalpha_mod_sys_analyser.report.excel_template import generate_xlsx_reports


PRESSURE_TEST_PERIOD = {
    "打击壳价值": (datetime.date(2016, 11, 1), datetime.date(2018, 2, 1)),
    "公募基金抱团": (datetime.date(2020, 10, 9), datetime.date(2021, 3, 1)),
    "行业风格切换": (datetime.date(2021, 9, 1), datetime.date(2021, 12, 31)),
    "小盘踩踏危机": (datetime.date(2024, 1, 5), datetime.date(2024, 2, 8)),
}


def _returns(unit_net_value: Series):
    return (unit_net_value / unit_net_value.shift(1).fillna(1)).fillna(0) - 1


def _yearly_indicators(
        p_nav: Series, p_returns: Series, b_nav: Optional[Series], b_returns: Optional[Series], risk_free_rates: Dict
):
    data = defaultdict(list)

    for year, p_year_returns in p_returns.groupby(p_returns.index.year):  # noqa
        year_slice = p_returns.index.year == year  # noqa
        if b_nav is not None:
            # 周胜率
            b_year_returns = b_returns[year_slice]
            weekly_p_returns = _returns(p_nav[year_slice].resample("W").last().dropna())
            weekly_b_returns = _returns(b_nav[year_slice].resample("W").last().dropna())
            weekly_risk = Risk(weekly_p_returns, weekly_b_returns, risk_free_rates[year], period=WEEKLY)
            weekly_excess_win_rate = weekly_risk.excess_win_rate

            # 月胜率
            monthly_p_returns = _returns(p_nav[year_slice].resample("M").last().dropna())
            monthly_b_returns = _returns(b_nav[year_slice].resample("M").last().dropna())
            monthly_risk = Risk(monthly_p_returns, monthly_b_returns, risk_free_rates[year], period=MONTHLY)
            monthly_excess_win_rate = monthly_risk.excess_win_rate
        else:
            weekly_excess_win_rate = numpy.nan
            monthly_excess_win_rate = numpy.nan
            b_year_returns = Series(index=p_year_returns.index)
        excess_nav = (p_year_returns + 1).cumprod() / (b_year_returns + 1).cumprod()
        excess_max_dd = _max_dd(excess_nav.values, excess_nav.index)
        max_dd = _max_dd(p_nav[year_slice].values, p_nav[year_slice].index)
        risk = Risk(p_year_returns, b_year_returns, risk_free_rates[year])
        data["year"].append(year)
        data["returns"].append(risk.return_rate)
        data["benchmark_returns"].append(risk.benchmark_return)
        data["geometric_excess_return"].append(risk.geometric_excess_return)
        data["geometric_excess_drawdown"].append(risk.geometric_excess_drawdown)
        data["geometric_excess_drawdown_days"].append((excess_max_dd.end_date - excess_max_dd.start_date).days)
        data["sharpe_ratio"].append(risk.sharpe)
        data["excess_sharpe"].append(risk.excess_sharpe)
        data["information_ratio"].append(risk.information_ratio)
        data["annual_tracking_error"].append(risk.annual_tracking_error)
        data["weekly_excess_win_rate"].append(weekly_excess_win_rate)
        data["monthly_excess_win_rate"].append(monthly_excess_win_rate)
        data["excess_annual_volatility"].append(risk.excess_annual_volatility)
        data["annual_volatility"].append(risk.annual_volatility)
        data["max_drawdown"].append(risk.max_drawdown)
        data["max_drawdown_days"].append((max_dd.end_date - max_dd.start_date).days)
        data["alpha"].append(risk.alpha)
        data["beta"].append(risk.beta)
    return data


def _monthly_returns(p_returns: Series):
    data = DataFrame(index=p_returns.index.year.unique(), columns=list(range(1, 13)))
    for year, p_year_returns in p_returns.groupby(p_returns.index.year):
        for month, p_month_returns in p_year_returns.groupby(p_year_returns.index.month):
            data.loc[year, month] = (p_month_returns + 1).prod() - 1
    data["cum"] = ((data.fillna(0) + 1).cumprod(axis=1) - 1)[12]
    return ChainMap({str(c): data[c] for c in data.columns}, {"year": data.index})


def _monthly_geometric_excess_returns(p_returns: Series, b_returns: Optional[Series]):
    if b_returns is None:
        return {}
    data = DataFrame(index=p_returns.index.year.unique(), columns=list(range(1, 13)))
    for year, p_year_returns in p_returns.groupby(p_returns.index.year):
        for month, p_month_returns in p_year_returns.groupby(p_year_returns.index.month):
            b_month_returns = b_returns.loc[p_month_returns.index]
            data.loc[year, month] = (p_month_returns + 1).prod() / (b_month_returns + 1).prod() - 1
        b_year_returns = b_returns.loc[p_year_returns.index]
        data.loc[year, "cum"] = (p_year_returns + 1).prod() / (b_year_returns + 1).prod() - 1
    return ChainMap({str(c): data[c] for c in data.columns}, {"year": data.index})


def _gen_positions_weight(df):
    rename = {"{}%".format(i): "percent_{}".format(i) for i in [25, 50, 75]}
    return df.reset_index().rename(columns=rename).to_dict(orient="list")


def _pressure_test(
        p_nav: Series, p_returns: Series, b_nav: Optional[Series], b_returns: Optional[Series]
    ):
    env = Environment.get_instance()
    # data = {field: [] for field in [
    #     "title", "start_date", "end_date", "returns", "annual_return", "geometric_excess_return", "max_drawdown",
    #     "geometric_excess_drawdown", "sharpe", "excess_sharpe"
    # ]}
    data = defaultdict(list)
    
    for title, (start, end) in PRESSURE_TEST_PERIOD.items():
        p_period_returns = p_returns.loc[start: end]
        if (p_period_returns is None or p_period_returns.empty):
            continue
        # 当且仅当回测周期完整包含压力测试的一个区间时才展示该区间的表现
        if len(p_period_returns) != len(env.data_proxy.get_trading_dates(start, end)):
            continue
        if b_nav is not None:
            b_period_returns = b_returns.loc[start: end]
        else:
            b_period_returns = Series(index=p_period_returns.index)
        risk_free_rate = env.data_proxy.get_risk_free_rate(start, end)
        risk = Risk(p_period_returns, b_period_returns, risk_free_rate)
        data["title"].append(title)
        data["start_date"].append(str(start))
        data["end_date"].append(str(end))
        data["returns"].append(risk.return_rate)
        data["annual_return"].append(risk.annual_return)
        data["geometric_excess_return"].append(risk.geometric_excess_return)
        data["max_drawdown"].append(risk.max_drawdown)
        data["geometric_excess_drawdown"].append(risk.geometric_excess_drawdown)
        data["sharpe"].append(risk.sharpe)
        data["excess_sharpe"].append(risk.excess_sharpe)
    if not data["title"]:
        return None
    return data


def generate_report(result_dict, output_path):
    from six import StringIO

    try:
        os.mkdir(output_path)
    except:
        pass

    summary = result_dict["summary"]
    portfolio = result_dict["portfolio"]
    p_nav = portfolio.unit_net_value
    p_returns = _returns(p_nav)
    if "benchmark_portfolio" in result_dict:
        benchmark_portfolio = result_dict["benchmark_portfolio"]
        b_nav = benchmark_portfolio.unit_net_value
        b_returns = _returns(b_nav)
    else:
        b_nav = b_returns = None
    generate_xlsx_reports({
        "概览": summary,
        "年度指标": _yearly_indicators(p_nav, p_returns, b_nav, b_returns, result_dict["yearly_risk_free_rates"]),
        "月度收益": _monthly_returns(p_returns),
        "月度超额收益（几何）": _monthly_geometric_excess_returns(p_returns, b_returns),
        "个股权重": _gen_positions_weight(result_dict["positions_weight"]),
        "压力测试": _pressure_test(p_nav, p_returns, b_nav, b_returns),
    }, output_path)

    for name in ["portfolio", "stock_account", "future_account",
                 "stock_positions", "future_positions", "trades", "positions_weight"]:
        try:
            df = result_dict[name]
        except KeyError:
            continue

        # replace all date in dataframe as string
        if df.index.name == "date":
            df = df.reset_index()
            df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
            df = df.set_index("date")

        if pandas.__version__ >= '1.5.0':
            df.to_csv("{}/{}.csv".format(output_path, name), encoding='utf-8-sig', lineterminator='\n')
        else:
            # pandas 1.5.0 以下是 line_terminator
            df.to_csv("{}/{}.csv".format(output_path, name), encoding='utf-8-sig', line_terminator='\n')

if __name__ == "__main__":
    import pickle
    result = pickle.load(open("result.pkl", "rb"))
    generate_report(result, "..")
