# -*- coding: utf-8 -*-
# 版权所有 2021 深圳米筐科技有限公司（下称“米筐科技”）
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
from typing import List, Mapping, Tuple
from collections import ChainMap

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import gridspec, ticker, image as mpimg, pyplot as plt

import rqalpha

from .utils import IndicatorInfo, LineInfo, IndexRange, max_ddd as _max_ddd, max_dd as _max_dd, weekly_returns, MaxDDInfo
from .consts import INDICATOR_WIDTH, INDICATOR_VALUE_HEIGHT, INDICATOR_LABEL_HEIGHT, IMG_WIDTH
from .consts import LABEL_FONT_SIZE, BLACK
from .consts import INDICATORS, WEEKLY_INDICATORS, EXCESS_INDICATORS
from .consts import LINE_BENCHMARK, LINE_STRATEGY, LINE_WEEKLY_BENCHMARK, LINE_WEEKLY, LINE_EXCESS, MAX_DD, MAX_DDD


class SubPlot:
    height: int

    def plot(self, ax: Axes):
        raise NotImplementedError


class IndicatorArea(SubPlot):
    height: int = 2

    def __init__(self, indicators: List[List[IndicatorInfo]], indicator_values: Mapping[str, float]):
        self._indicators = indicators
        self._values = indicator_values

    def plot(self, ax: Axes):
        ax.axis("off")
        for lineno, indicators in enumerate(self._indicators[::-1]):  # lineno: 自下而上的行号
            for index_in_line, i in enumerate(indicators):
                x = index_in_line * INDICATOR_WIDTH
                y_value = lineno * (INDICATOR_VALUE_HEIGHT + INDICATOR_LABEL_HEIGHT)
                y_label = y_value + INDICATOR_LABEL_HEIGHT
                try:
                    value = i.formatter.format(self._values[i.key])
                except KeyError:
                    value = "nan"
                ax.text(x, y_label, i.label, color=i.color, fontsize=LABEL_FONT_SIZE),
                ax.text(x, y_value, value, color=BLACK, fontsize=i.value_font_size)


class ReturnPlot(SubPlot):
    height: int = 4
    returns_line_width = 2

    def __init__(self, returns, returns_lines: List[Tuple[pd.Series, LineInfo]], max_dds: List[Tuple[IndexRange, MaxDDInfo]]):
        self._returns = returns
        self._returns_lines = returns_lines
        self._max_dds = max_dds

    @classmethod
    def _plot_returns(cls, ax, returns, label, color, alpha=1):
        if returns is not None:
            ax.plot(returns, label=label, alpha=alpha, linewidth=cls.returns_line_width, color=color)

    def plot(self, ax: Axes):
        ax.get_xaxis().set_minor_locator(ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(b=True, which='minor', linewidth=.2)
        ax.grid(b=True, which='major', linewidth=1)
        ax.patch.set_alpha(0.6)
        # plot lines
        for returns, (label, color, alpha) in self._returns_lines:
            if returns is not None:
                ax.plot(returns, label=label, alpha=alpha, linewidth=self.returns_line_width, color=color)
        # plot MaxDD/MaxDDD
        for max_dd, (label, marker, color, markersize, alpha) in self._max_dds:
            ax.plot(
                [max_dd.start_date, max_dd.end_date], [self._returns[max_dd.start], self._returns[max_dd.end]],
                marker, color=color, markersize=markersize, alpha=alpha, label=label
            )
        # place legend
        plt.legend(loc="best").get_frame().set_alpha(0.5)
        # manipulate axis
        ax.set_yticklabels(['{:3.2f}%'.format(x * 100) for x in ax.get_yticks()])


class UserPlot(SubPlot):
    height: int = 2

    def __init__(self, plots_df):
        self._df = plots_df

    def plot(self, ax: Axes):
        ax.patch.set_alpha(0.6)
        for column in self._df.columns:
            ax.plot(self._df[column], label=column)
        plt.legend(loc="best").get_frame().set_alpha(0.5)


class WaterMark:
    def __init__(self, img_width, img_height):
        logo_file = os.path.join(
            os.path.dirname(os.path.realpath(rqalpha.__file__)),
            "resource", 'ricequant-logo.png')
        self.img_width = img_width
        self.img_height = img_height
        self.logo_img = mpimg.imread(logo_file)
        self.dpi = self.logo_img.shape[1] / img_width * 1.1

    def plot(self, fig: Figure):
        fig.figimage(
            self.logo_img,
            xo=(self.img_width * self.dpi - self.logo_img.shape[1]) / 2,
            yo=(self.img_height * self.dpi - self.logo_img.shape[0]) / 2,
            alpha=0.4,
        )


def plot_result(result_dict, show_windows=True, savefile=None, weekly_indicators: bool = False):
    summary = result_dict["summary"]
    title = summary['strategy_file']
    portfolio = result_dict["portfolio"]
    benchmark_portfolio = result_dict.get("benchmark_portfolio")
    max_dd = _max_dd(portfolio.unit_net_value.values, portfolio.index)
    max_ddd = _max_ddd(portfolio.unit_net_value.values, portfolio.index)
    # 超额收益
    return_lines: List[Tuple[pd.Series, LineInfo]] = [(portfolio.unit_net_value - 1, LINE_STRATEGY)]

    if benchmark_portfolio is not None:
        ex_returns = portfolio.unit_net_value - benchmark_portfolio.unit_net_value
        ex_max_dd = _max_dd(ex_returns + 1, portfolio.index)
        ex_max_ddd = _max_ddd(ex_returns + 1, portfolio.index)
        ex_max_dd_ddd = "MaxDD {}\nMaxDDD {}".format(ex_max_dd.repr, ex_max_ddd.repr)
        indicators = INDICATORS + [EXCESS_INDICATORS]
        return_lines.extend([
            (benchmark_portfolio.unit_net_value - 1, LINE_BENCHMARK),
            (ex_returns, LINE_EXCESS),
        ])
        if weekly_indicators:
            return_lines.append((weekly_returns(benchmark_portfolio), LINE_WEEKLY_BENCHMARK))
    else:
        ex_max_dd_ddd = "nan"
        indicators = INDICATORS
    if weekly_indicators:
        return_lines.append((weekly_returns(portfolio), LINE_WEEKLY))
        indicators.append(WEEKLY_INDICATORS)

    sub_plots = [IndicatorArea(indicators, ChainMap(summary, {
        "max_dd_ddd": "MaxDD {}\nMaxDDD {}".format(max_dd.repr, max_ddd.repr),
        "excess_max_dd_ddd": ex_max_dd_ddd,
    })), ReturnPlot(
        portfolio.unit_net_value - 1, return_lines, [(max_dd, MAX_DD), (max_ddd, MAX_DDD)]
    )]
    if "plots" in result_dict:
        sub_plots.append(UserPlot(result_dict["plots"]))

    img_height = sum(s.height for s in sub_plots)
    water_mark = WaterMark(IMG_WIDTH, img_height)
    fig = plt.figure(title, figsize=(IMG_WIDTH, img_height), dpi=water_mark.dpi)
    gs = gridspec.GridSpec(img_height, 8)
    last_height = 0
    for p in sub_plots:
        p.plot(plt.subplot(gs[last_height:last_height + p.height, :-1]))
        last_height += p.height
    water_mark.plot(fig)
    plt.tight_layout()

    if savefile:
        file_path = savefile
        if os.path.isdir(savefile):
            file_path = os.path.join(savefile, "{}.png".format(summary["strategy_name"]))
        plt.savefig(file_path, bbox_inches='tight')

    if show_windows:
        plt.show()


