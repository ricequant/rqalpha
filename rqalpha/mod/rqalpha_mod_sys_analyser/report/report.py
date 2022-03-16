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

import numpy
from collections import ChainMap
from pandas import Series, DataFrame

from rqrisk import Risk

from rqalpha.mod.rqalpha_mod_sys_analyser.report.excel_template import generate_xlsx_reports


def _returns(unit_net_value: Series):
    return (unit_net_value / unit_net_value.shift(1).fillna(1)).fillna(0) - 1


def _yearly_indicators(
        p_nav: Series, p_returns: Series, b_nav: Optional[Series], b_returns: Optional[Series], risk_free_rates: Dict
):
    data = {field: [] for field in [
        "year", "returns", "active_returns", "sharpe_ratio", "information_ratio", "weekly_win_rate"
    ]}

    for year, p_year_returns in p_returns.groupby(p_returns.index.year):  # noqa
        year_slice = p_returns.index.year == year  # noqa
        if b_nav is not None:
            # 周胜率
            b_year_returns = b_returns[year_slice]
            weekly_p_returns = _returns(p_nav[year_slice].resample("W").last().dropna())
            weekly_b_returns = _returns(b_nav[year_slice].resample("W").last().dropna())
            weekly_win_rate = (weekly_p_returns > weekly_b_returns).sum() / len(weekly_p_returns)
        else:
            weekly_win_rate = numpy.nan
            b_year_returns = Series(index=p_year_returns.index)
        risk = Risk(p_year_returns, b_year_returns, risk_free_rates[year])
        data["year"].append(year)
        data["returns"].append(risk.return_rate)
        data["active_returns"].append(risk.excess_return_rate)
        data["sharpe_ratio"].append(risk.sharpe)
        data["information_ratio"].append(risk.information_ratio)
        data["weekly_win_rate"].append(weekly_win_rate)
    return data


def _monthly_returns(p_returns: Series):
    data = DataFrame(index=p_returns.index.year.unique(), columns=list(range(1, 13)))
    for year, p_year_returns in p_returns.groupby(p_returns.index.year):
        for month, p_month_returns in p_year_returns.groupby(p_year_returns.index.month):
            data.loc[year, month] = (p_month_returns + 1).prod() - 1
    return ChainMap({str(c): data[c] for c in data.columns}, {"year": data.index})


def _monthly_active_returns(p_returns: Series, b_returns: Optional[Series]):
    if b_returns is None:
        return {}
    return _monthly_returns(p_returns - b_returns)


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
        "月度主动收益": _monthly_active_returns(p_returns, b_returns)
    }, output_path)

    for name in ["portfolio", "stock_account", "future_account",
                 "stock_positions", "future_positions", "trades"]:
        try:
            df = result_dict[name]
        except KeyError:
            continue

        # replace all date in dataframe as string
        if df.index.name == "date":
            df = df.reset_index()
            df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
            df = df.set_index("date")

        csv_txt = StringIO()
        csv_txt.write(df.to_csv(encoding='utf-8', line_terminator='\n'))

        with open(os.path.join(output_path, "{}.csv".format(name)), 'w') as csvfile:
            csvfile.write(csv_txt.getvalue())


if __name__ == "__main__":
    import pickle
    result = pickle.load(open("result.pkl", "rb"))
    generate_report(result, "..")
