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
from typing import List, Mapping, Tuple, Sequence, Optional
from collections import ChainMap

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib import gridspec, ticker, image as mpimg, pyplot

import rqalpha
from rqalpha.const import POSITION_EFFECT
from .utils import IndicatorInfo, LineInfo, max_dd as _max_dd, SpotInfo, max_ddd as _max_ddd
from .utils import weekly_returns, trading_dates_index
from .consts import PlotTemplate, DefaultPlot
from .consts import IMG_WIDTH, INDICATOR_AREA_HEIGHT, PLOT_AREA_HEIGHT, USER_PLOT_AREA_HEIGHT, PLOT_TITLE_HEIGHT
from .consts import LABEL_FONT_SIZE, BLACK, SUPPORT_CHINESE, TITLE_FONT_SIZE
from .consts import MAX_DD, MAX_DDD, OPEN_POINT, CLOSE_POINT
from .consts import LINE_BENCHMARK, LINE_STRATEGY, LINE_WEEKLY_BENCHMARK, LINE_WEEKLY, LINE_EXCESS


class SubPlot:
    height: int
    right_pad: Optional[int] = None

    def plot(self, ax: Axes):
        raise NotImplementedError


class IndicatorArea(SubPlot):
    height: int = INDICATOR_AREA_HEIGHT
    right_pad = -1

    def __init__(
            self, indicators: List[List[IndicatorInfo]], indicator_values: Mapping[str, float],
            plot_template: PlotTemplate, strategy_name=None
    ):
        self._indicators = indicators
        self._values = indicator_values
        self._template = plot_template
        self._strategy_name = strategy_name

    def plot(self, ax: Axes):
        ax.axis("off")
        for lineno, indicators in enumerate(self._indicators[::-1]):  # lineno: 自下而上的行号
            _extra_width = 0  # 用于保存加长的部分, 原因是部分label太长出现覆盖
            for index_in_line, i in enumerate(indicators):
                _extra_width += (i.label_width_multiplier - 1) * self._template.INDICATOR_WIDTH
                x = index_in_line * self._template.INDICATOR_WIDTH + _extra_width
                y_value = lineno * (self._template.INDICATOR_VALUE_HEIGHT + self._template.INDICATOR_LABEL_HEIGHT)
                y_label = y_value + self._template.INDICATOR_LABEL_HEIGHT
                try:
                    value = i.formatter.format(self._values[i.key])
                except KeyError:
                    value = "nan"
                ax.text(x, y_label, i.label, color=i.color, fontsize=LABEL_FONT_SIZE),
                ax.text(x, y_value, value, color=BLACK, fontsize=i.value_font_size)
        if self._strategy_name:
            p = TitlePlot(self._strategy_name, len(self._indicators), self._template)
            p.plot(ax)
        

class ReturnPlot(SubPlot):
    height: int = PLOT_AREA_HEIGHT

    def __init__(
            self,
            returns,
            lines: List[Tuple[pd.Series, LineInfo]],
            spots_on_returns: List[Tuple[Sequence[int], SpotInfo]],
            log_scale: bool
    ):
        self._returns = returns
        self._lines = lines
        self._spots_on_returns = spots_on_returns
        self._log_scale = log_scale

    @classmethod
    def _plot_line(cls, ax, returns, info: LineInfo):
        if returns is not None:
            ax.plot(returns, label=info.label, alpha=info.alpha, linewidth=info.linewidth, color=info.color)

    def _plot_spots_on_returns(self, ax, positions: Sequence[int], info: SpotInfo):
        return_or_net_values = self._returns[positions] if not self._log_scale else 1 + self._returns[positions]
        ax.plot(
            self._returns.index[positions], return_or_net_values,
            info.marker, color=info.color, markersize=info.markersize, alpha=info.alpha, label=info.label
        )

    def plot(self, ax: Axes):
        ax.grid(visible=True, which='minor', linewidth=.2)
        ax.grid(visible=True, which='major', linewidth=1)
        ax.patch.set_alpha(0.6)

        # plot lines
        for returns, info in self._lines:
            return_or_net_values = returns if not self._log_scale else 1 + returns
            self._plot_line(ax, return_or_net_values, info)
        # plot MaxDD/MaxDDD
        for positions, info in self._spots_on_returns:
            self._plot_spots_on_returns(ax, positions, info)

        # place legend
        pyplot.legend(loc="best").get_frame().set_alpha(0.5)

        # manipulate axis
        ax.get_xaxis().set_minor_locator(ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(ticker.AutoMinorLocator())
        if self._log_scale:
            ax.set_yscale('log')
            ax.yaxis.set_major_locator(ticker.AutoLocator())
            formatter = ticker.FuncFormatter(lambda x, _: '{:3.2f}%'.format((x - 1) * 100))
            ax.yaxis.set_major_formatter(formatter)
            ax.yaxis.set_minor_formatter(formatter)
        else:
            ax.set_yticks(ax.get_yticks())  # make matplotlib happy
            ax.set_yticklabels(['{:3.2f}%'.format(x * 100) for x in ax.get_yticks()])


class UserPlot(SubPlot):
    height: int = USER_PLOT_AREA_HEIGHT

    def __init__(self, plots_df):
        self._df = plots_df

    def plot(self, ax: Axes):
        ax.patch.set_alpha(0.6)
        for column in self._df.columns:
            ax.plot(self._df[column], label=column)
        pyplot.legend(loc="best").get_frame().set_alpha(0.5)


class TitlePlot(SubPlot):
    height: int = PLOT_TITLE_HEIGHT

    def __init__(self, strategy_name, indicator_area_rows, plot_template: PlotTemplate):
        self._strategy_name = strategy_name
        self._indicator_area_rows = indicator_area_rows
        self._template = plot_template

    def plot(self, ax:Axes):
        x = 0.57  # title 为整图居中，而非子图居中
        y = (self._template.INDICATOR_LABEL_HEIGHT + self._template.INDICATOR_VALUE_HEIGHT) * self._indicator_area_rows + 0.1
        ax.text(x, y, self._strategy_name, ha='center', va='bottom', color=BLACK, fontsize=TITLE_FONT_SIZE)

class WaterMark:
    def __init__(self, img_width, img_height, strategy_name):
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
            xo = (self.img_width * self.dpi - self.logo_img.shape[1]) / 2,
            yo = (PLOT_AREA_HEIGHT * self.dpi - self.logo_img.shape[0]) / 2, 
            alpha=0.4
            )


def _plot(title: str, sub_plots: List[SubPlot], strategy_name):
    img_height = sum(s.height for s in sub_plots)
    water_mark = WaterMark(IMG_WIDTH, img_height, strategy_name)
    fig = pyplot.figure(title, figsize=(IMG_WIDTH, img_height), dpi=water_mark.dpi, clear=True)
    water_mark.plot(fig)

    gs = gridspec.GridSpec(img_height, 8, figure=fig)
    last_height = 0
    for p in sub_plots:
        p.plot(pyplot.subplot(gs[last_height:last_height + p.height, :p.right_pad]))
        last_height += p.height

    pyplot.tight_layout()
    return fig


def plot_result(
        result_dict, show=True, save=None, weekly_indicators: bool = False, open_close_points: bool = False,
        plot_template_cls=DefaultPlot, strategy_name=None, log_scale: bool = False
):
    summary = result_dict["summary"]
    portfolio = result_dict["portfolio"]

    return_lines: List[Tuple[pd.Series, LineInfo]] = [(portfolio.unit_net_value - 1, LINE_STRATEGY)]
    if "benchmark_portfolio" in result_dict:
        benchmark_portfolio = result_dict["benchmark_portfolio"]
        plot_template = plot_template_cls(portfolio.unit_net_value, benchmark_portfolio.unit_net_value)
        ex_returns = plot_template.geometric_excess_returns
        ex_max_dd_ddd = "MaxDD {}\nMaxDDD {}".format(
            _max_dd(ex_returns + 1, portfolio.index).repr, _max_ddd(ex_returns + 1, portfolio.index).repr
        )
        indicators = plot_template.INDICATORS + plot_template.EXCESS_INDICATORS

        # 在图例中输出基准信息
        _b_str = summary["benchmark_symbol"] if SUPPORT_CHINESE else summary["benchmark"]
        _INFO = LineInfo(
            LINE_BENCHMARK.label + "({})".format(_b_str), LINE_BENCHMARK.color,
            LINE_BENCHMARK.alpha, LINE_BENCHMARK.linewidth
        )

        return_lines.extend([
            (benchmark_portfolio.unit_net_value - 1, _INFO),
            (ex_returns, LINE_EXCESS),
        ])
        if weekly_indicators:
            return_lines.append((weekly_returns(benchmark_portfolio), LINE_WEEKLY_BENCHMARK))
    else:
        ex_max_dd_ddd = "nan"
        plot_template = plot_template_cls(portfolio.unit_net_value, None)
        indicators = plot_template.INDICATORS
    if weekly_indicators:
        return_lines.append((weekly_returns(portfolio), LINE_WEEKLY))
        indicators.extend(plot_template.WEEKLY_INDICATORS)
    max_dd = _max_dd(portfolio.unit_net_value.values, portfolio.index)
    max_ddd = summary["max_drawdown_duration"]
    spots_on_returns: List[Tuple[Sequence[int], SpotInfo]] = [
        ([max_dd.start, max_dd.end], MAX_DD),
        ([max_ddd.start, max_ddd.end], MAX_DDD)
    ]
    if open_close_points and not result_dict["trades"].empty:
        trades: pd.DataFrame = result_dict["trades"]
        spots_on_returns.append((trading_dates_index(trades, POSITION_EFFECT.CLOSE, portfolio.index), CLOSE_POINT))
        spots_on_returns.append((trading_dates_index(trades, POSITION_EFFECT.OPEN, portfolio.index), OPEN_POINT))

    sub_plots = [IndicatorArea(indicators, ChainMap(summary, {
        "max_dd_ddd": "MaxDD {}\nMaxDDD {}".format(max_dd.repr, max_ddd.repr),
        "excess_max_dd_ddd": ex_max_dd_ddd,
    }), plot_template, strategy_name), ReturnPlot(
        portfolio.unit_net_value - 1, return_lines, spots_on_returns, log_scale
    )]
    if "plots" in result_dict:
        sub_plots.append(UserPlot(result_dict["plots"]))
    
    if strategy_name:
        for p in sub_plots:
            if (isinstance(p, IndicatorArea)): p.height += PLOT_TITLE_HEIGHT

    _plot(summary["strategy_file"], sub_plots, strategy_name)

    if save:
        file_path = save
        if os.path.isdir(save):
            file_path = os.path.join(save, "{}.png".format(summary["strategy_name"]))
        pyplot.savefig(file_path, bbox_inches='tight')

    if show:
        pyplot.show()
