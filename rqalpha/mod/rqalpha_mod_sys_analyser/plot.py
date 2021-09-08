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
from collections import namedtuple, ChainMap

import numpy as np
import pandas as pd
from matplotlib import rcParams, gridspec, ticker, image as mpimg, pyplot as plt
from matplotlib.font_manager import findfont, FontProperties

import rqalpha
from rqalpha.utils.logger import system_log
from rqalpha.utils.i18n import gettext as _

plt.style.use('ggplot')

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = [
    'Microsoft Yahei', 'Heiti SC', 'Heiti TC', 'STHeiti', 'WenQuanYi Zen Hei',
    'WenQuanYi Micro Hei', "文泉驿微米黑", 'SimHei', 'Arial Unicode MS'
] + rcParams['font.sans-serif']
rcParams['axes.unicode_minus'] = False

font = findfont(FontProperties(family=['sans-serif']))
if "/matplotlib/" in font:
    system_log.warn("PLOT: Missing Chinese fonts. Fallback to English.")
    LABEL_FONT_SIZE = 8
    _ = lambda txt: txt
else:
    LABEL_FONT_SIZE = 10

# 三部分的高度
PLOT_AREA_HEIGHT = 4
USER_PLOT_AREA_HEIGHT = 2

IMG_WIDTH = 13

Heights = namedtuple("Heights", ("label", "value"))
Indicator = namedtuple("Indicator", ("key", "label", "color", "formatter", "value_font_size"))

RED = "#aa4643"
LIGHT_CORAL = "#F08080"
BLUE = "#4572a7"
YELLOW = "#F3A423"
BLACK = "#000000"

# 指标的高度值
INDICATOR_Y_POS = [
    Heights(1.3, 1.15),
    Heights(0.95, 0.8),
    Heights(0.6, 0.45),
    Heights(0.25, 0.10),
]
INDICATOR_X_POS = [0.15 * i for i in range(7)]

INDICATORS = [[
    Indicator("total_returns", _("TotalReturns"), RED, "{0:.3%}", 11),
    Indicator("annualized_returns", _("AnnualReturns"), RED, "{0:.3%}", 11),
    Indicator("alpha", _("Alpha"), BLACK, "{0:.4}", 11),
    Indicator("beta", _("Beta"), BLACK, "{0:.4}", 11),
    Indicator("sharpe", _("Sharpe"), BLACK, "{0:.4}", 11),
    Indicator("sortino", _("Sortino"), BLACK, "{0:.4}", 11),
    Indicator("information_ratio", _("InformationRatio"), BLACK, "{0:.4}", 11),
],[
    Indicator("benchmark_total_returns", _("BenchmarkReturns"), BLUE, "{0:.3%}", 11),
    Indicator("benchmark_annualized_returns", _("BenchmarkAnnual"), BLUE, "{0:.3%}", 11),
    Indicator("volatility", _("Volatility"), BLACK, "{0:.4}", 11),
    Indicator("max_drawdown", _("MaxDrawdown"), BLACK, "{0:.4}", 11),
    Indicator("tracking_error", _("TrackingError"), BLACK, "{0:.4}", 11),
    Indicator("downside_risk", _("DownsideRisk"), BLACK, "{0:.4}", 11),
    Indicator("max_dd_ddd", _("MaxDD/MaxDDD"), BLACK, "{}", 6),
], [
    Indicator("weekly_alpha", _("WeeklyAlpha"), BLACK, "{0:.4}", 11),
    Indicator("weekly_beta", _("WeeklyBeta"), BLACK, "{0:.4}", 11),
    Indicator("weekly_sharpe", _("WeeklySharpe"), BLACK, "{0:.4}", 11),
    Indicator("weekly_sortino", _("WeeklySortino"), BLACK, "{0:.4}", 11),
    Indicator("weekly_information_ratio", _("WeeklyInfoRatio"), BLACK, "{0:.4}", 11),
    Indicator("weekly_tracking_error", _("WeeklyTrackingError"), BLACK, "{0:.4}", 11),
    Indicator("weekly_max_drawdown", _("WeeklyMaxDrawdown"), BLACK, "{0:.4}", 11),
]]

excess_indicators = [
    Indicator("excess_returns", _("ExcessReturns"), RED, "{0:.3%}", 11),
    Indicator("excess_annual_returns", _("ExcessAnnual"), RED, "{0:.3%}", 11),
    Indicator("excess_sharpe", _("ExcessSharpe"), BLACK, "{0:.4}", 11),
    Indicator("excess_volatility", _("ExcessVolatility"), BLACK, "{0:.4}", 11),
    Indicator("excess_annual_volatility", _("ExcessAnnualVolatility"), BLACK, "{0:.4}", 11),
    Indicator("excess_max_drawdown", _("ExcessMaxDD"), BLACK, "{0:.4}", 11),
    Indicator("excess_max_dd_ddd", _("ExcessMaxDD/ExcessMaxDDD"), BLACK, "{}", 6),
]


class IndexRange(namedtuple("IndexRange", ("start", "end", "start_date", "end_date"))):
    @classmethod
    def new(cls, start, end, index):
        return cls(start, end, index[start].date(), index[end].date())

    @property
    def repr(self):
        return "{}~{}, {} days".format(self.start_date, self.end_date, (self.end_date - self.start_date).days)

    def plot(self, ax, returns, marker, color, label):
        ax.plot(
            [self.start_date, self.end_date], [returns[self.start], returns[self.end]],
            marker, color=color, markersize=8, alpha=.7, label=label
        )


def _max_dd(arr, index):
    # type: (np.array, pd.DatetimeIndex) -> IndexRange
    end = np.argmax(np.maximum.accumulate(arr) / arr)
    if end == 0:
        end = len(arr) - 1
    start = np.argmax(arr[:end]) if end > 0 else 0
    return IndexRange.new(start, end, index)


def _max_ddd(arr, index):
    # type: (np.array, pd.DatetimeIndex) -> IndexRange
    max_seen = arr[0]
    ddd_start, ddd_end = 0, 0
    ddd = 0
    start = 0
    in_draw_down = False

    i = 0
    for i in range(len(arr)):
        if arr[i] > max_seen:
            if in_draw_down:
                in_draw_down = False
                if i - start > ddd:
                    ddd = i - start
                    ddd_start = start
                    ddd_end = i - 1
            max_seen = arr[i]
        elif arr[i] < max_seen:
            if not in_draw_down:
                in_draw_down = True
                start = i - 1

    if arr[i] < max_seen:
        if i - start > ddd:
            return IndexRange.new(start, i, index)

    return IndexRange.new(ddd_start, ddd_end, index)


def _plot_indicators(ax, indicator_values, plot_excess_indicators):
    ax.axis("off")
    if plot_excess_indicators:
        all_indicators = INDICATORS + [excess_indicators]
    else:
        all_indicators = [[]] + INDICATORS

    for lineno, indicators in enumerate(all_indicators):
        for index_in_line, i in enumerate(indicators):
            x = INDICATOR_X_POS[index_in_line]
            y = INDICATOR_Y_POS[lineno]
            try:
                value = i.formatter.format(indicator_values[i.key])
            except KeyError:
                value = "nan"
            ax.text(x, y.label, i.label, color=i.color, fontsize=LABEL_FONT_SIZE),
            ax.text(x, y.value, value, color=BLACK, fontsize=i.value_font_size)


def _plot_returns(ax, returns, b_returns, excess_returns, weekly_returns, weekly_b_returns, max_dd, max_ddd):
    ax.get_xaxis().set_minor_locator(ticker.AutoMinorLocator())
    ax.get_yaxis().set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(b=True, which='minor', linewidth=.2)
    ax.grid(b=True, which='major', linewidth=1)
    ax.patch.set_alpha(0.6)

    # plot lines
    ax.plot(returns, label=_(u"Strategy"), alpha=1, linewidth=2, color=RED)
    if b_returns is not None:
        ax.plot(b_returns, label=_(u"Benchmark"), alpha=1, linewidth=2, color=BLUE)
    if excess_returns is not None:
        ax.plot(excess_returns, label=_(u"Excess"), alpha=1, linewidth=2, color=YELLOW)
    ax.plot(weekly_returns, label=_("Weekly"), alpha=0.6, linewidth=2, color=RED)
    if weekly_b_returns is not None:
        ax.plot(weekly_b_returns, label=_("BenchmarkWeekly"), alpha=0.6, linewidth=2, color=BLUE)

    # plot MaxDD/MaxDDD
    max_dd.plot(ax, returns, "v", "Green", _("MaxDrawdown"))
    max_ddd.plot(ax, returns, "D", "Blue", _("MaxDDD"))

    # place legend
    leg = plt.legend(loc="best")
    leg.get_frame().set_alpha(0.5)

    # manipulate axis
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:3.2f}%'.format(x * 100) for x in vals])


def _plot_user_plots(ax, plots_df):
    ax.patch.set_alpha(0.6)
    for column in plots_df.columns:
        ax.plot(plots_df[column], label=column)

    leg = plt.legend(loc="best")
    leg.get_frame().set_alpha(0.5)


def plot_result(result_dict, show_windows=True, savefile=None):
    summary = result_dict["summary"]

    if "plots" in result_dict:
        indicator_area_height = 3
        img_height = indicator_area_height + PLOT_AREA_HEIGHT + USER_PLOT_AREA_HEIGHT + 1
    else:
        indicator_area_height = 2
        img_height = indicator_area_height + PLOT_AREA_HEIGHT

    logo_file = os.path.join(
        os.path.dirname(os.path.realpath(rqalpha.__file__)),
        "resource", 'ricequant-logo.png')
    logo_img = mpimg.imread(logo_file)
    dpi = logo_img.shape[1] / IMG_WIDTH * 1.1

    title = summary['strategy_file']
    fig = plt.figure(title, figsize=(IMG_WIDTH, img_height), dpi=dpi)

    gs = gridspec.GridSpec(img_height, 8)

    portfolio = result_dict["portfolio"]
    benchmark_portfolio = result_dict.get("benchmark_portfolio")
    max_dd = _max_dd(portfolio.unit_net_value.values, portfolio.index)
    max_ddd = _max_ddd(portfolio.unit_net_value.values, portfolio.index)
    # 超额收益
    if benchmark_portfolio is not None:
        ex_returns = portfolio.unit_net_value - benchmark_portfolio.unit_net_value
        ex_max_dd = _max_dd(ex_returns + 1, portfolio.index)
        ex_max_ddd = _max_ddd(ex_returns + 1, portfolio.index)
        ex_max_dd_ddd = "MaxDD {}\nMaxDDD {}".format(ex_max_dd.repr, ex_max_ddd.repr)
        plot_excess_indicators = True
        benchmark_weekly_portfolio = benchmark_portfolio.unit_net_value.reset_index().resample(
            "W", on="date").last().set_index("date").unit_net_value.dropna() - 1
    else:
        ex_max_dd_ddd = "nan"
        ex_returns = None
        benchmark_weekly_portfolio = None
        plot_excess_indicators = False

    _plot_indicators(
        plt.subplot(gs[:indicator_area_height, :-1]),
        ChainMap(summary, {
            "max_dd_ddd": "MaxDD {}\nMaxDDD {}".format(max_dd.repr, max_ddd.repr),
            "excess_max_dd_ddd": ex_max_dd_ddd,
        }),
        plot_excess_indicators
    )

    _plot_returns(
        plt.subplot(gs[indicator_area_height: PLOT_AREA_HEIGHT + indicator_area_height, :]),
        portfolio.unit_net_value - 1,
        None if benchmark_portfolio is None else benchmark_portfolio["unit_net_value"] - 1,
        ex_returns,
        portfolio.unit_net_value.reset_index().resample(
            "W", on="date").last().set_index("date").unit_net_value.dropna() - 1,
        benchmark_weekly_portfolio,
        max_dd,
        max_ddd
    )

    if "plots" in result_dict:
        _plot_user_plots(
            plt.subplot(gs[indicator_area_height + PLOT_AREA_HEIGHT + 1:, :]),
            result_dict["plots"]
        )

    # logo as watermark
    fig.figimage(
        logo_img,
        xo=((IMG_WIDTH * dpi) - logo_img.shape[1]) / 2,
        yo=(img_height * dpi - logo_img.shape[0]) / 2,
        alpha=0.4,
    )

    if savefile:
        fnmame = savefile
        if os.path.isdir(savefile):
            fnmame = os.path.join(savefile, "{}.png".format(summary["strategy_name"]))
        plt.savefig(fnmame, bbox_inches='tight')

    if show_windows:
        plt.show()


if __name__ == "__main__":
    import pickle
    with open("result.pkl", "rb") as f:
        plot_result(pickle.loads(f.read()))
