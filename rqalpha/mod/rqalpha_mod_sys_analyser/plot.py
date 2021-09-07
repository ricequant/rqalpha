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

from collections import namedtuple, ChainMap

import numpy as np
import pandas as pd

import rqalpha
from rqalpha.utils.logger import system_log
from rqalpha.utils.i18n import gettext

Heights = namedtuple("Heights", ("label", "value"))
Indicator = namedtuple("Indicator", ("key", "label", "color", "formatter", "value_font_size"))



RED = "#aa4643"
BLUE = "#4572a7"
BLACK = "#000000"
CHINESE_LABEL_FONT_SIZE = 12
ENGLISH_LABEL_FONT_SIZE = 9
CHINESE_FONTS = [
    'Microsoft Yahei', 'Heiti SC', 'Heiti TC', 'STHeiti', 'WenQuanYi Zen Hei',
    'WenQuanYi Micro Hei', "文泉驿微米黑", 'SimHei',
]

# 指标的高度值
INDICATOR_Y_POS = [
    Heights(0.8, 0.6),  # 第一行
    Heights(0.35, 0.15)  # 第二行
]
INDICATOR_X_POS = [0.15 * i for i in range(7)]

INDICATORS = [[  # 第一行指标
    Indicator("total_returns", "Total Returns", RED, "{0:.3%}", 12),
    Indicator("annualized_returns", "Annual Returns", RED, "{0:.3%}", 12),
    Indicator("alpha", "Alpha", BLACK, "{0:.4}", 12),
    Indicator("beta", "Beta", BLACK, "{0:.4}", 12),
    Indicator("sharpe", "Sharpe", BLACK, "{0:.4}", 12),
    Indicator("sortino", "Sortino", BLACK, "{0:.4}", 12),
    Indicator("information_ratio", "Information Ratio", BLACK, "{0:.4}", 12),
],[  # 第二行指标
    Indicator("benchmark_total_returns", "Benchmark Returns", BLUE, "{0:.4}", 12),
    Indicator("benchmark_annualized_returns", "Benchmark Annual", BLUE, "{0:.4}", 12),
    Indicator("volatility", "Volatility", BLACK, "{0:.4}", 12),
    Indicator("max_drawdown", "MaxDrawdown", BLACK, "{0:.4}",12),
    Indicator("tracking_error", "Tracking Error", BLACK, "{0:.4}", 12),
    Indicator("downside_risk", "Downside Risk", BLACK, "{0:.4}", 12),
    Indicator("max_dd_ddd", "MaxDD/MaxDDD", BLACK, "{0:.4}", 8),
]]


class IndexRange(namedtuple("IndexRange", ("start", "end", "start_date", "end_date"))):
    @classmethod
    def new(cls, start, end, index):
        return cls(start, end, index[start].date(), index[end].date())

    @property
    def repr(self):
        return "{}~{}, {} days".format(self.start_date, self.end_date, (self.end_date - self.start_date).days)

    def plot(self, ax, navs, marker, color, label):
        ax.plot(
            [self.start_date, self.end_date], [navs[self.start] - 1.0, navs[self.end] - 1.0],
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


def plot_result(result_dict, show_windows=True, savefile=None):
    import os
    from matplotlib import rcParams, gridspec, ticker, image as mpimg, pyplot as plt
    from matplotlib.font_manager import findfont, FontProperties
    plt.style.use('ggplot')

    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = CHINESE_FONTS + rcParams['font.sans-serif']
    rcParams['axes.unicode_minus'] = False

    font = findfont(FontProperties(family=['sans-serif']))
    if "/matplotlib/" in font:
        system_log.warn("Missing Chinese fonts. Fallback to English.")
        label_font_size = ENGLISH_LABEL_FONT_SIZE
        _ = lambda txt: txt
    else:
        label_font_size = CHINESE_LABEL_FONT_SIZE
        _ = gettext

    summary = result_dict["summary"]

    plots_area_size = 5 if "plots" in result_dict else 0
    img_width = 13
    img_height = 6 + int(plots_area_size * 0.9)

    logo_file = os.path.join(
        os.path.dirname(os.path.realpath(rqalpha.__file__)),
        "resource", 'ricequant-logo.png')
    logo_img = mpimg.imread(logo_file)
    dpi = logo_img.shape[1] / img_width * 1.1

    title = summary['strategy_file']
    fig = plt.figure(title, figsize=(img_width, img_height), dpi=dpi)
    gs = gridspec.GridSpec(10 + plots_area_size, 8)

    portfolio = result_dict["portfolio"]
    benchmark_portfolio = result_dict.get("benchmark_portfolio")
    index = portfolio.index
    portfolio_value = portfolio.unit_net_value * portfolio.units
    max_dd = _max_dd(portfolio_value.values, index)
    max_ddd = _max_ddd(portfolio_value.values, index)

    # drwa indicators
    indicator_values = ChainMap(
        summary,
        {"max_dd_ddd": "MaxDD {}\nMaxDDD{}".format(max_dd.repr, max_ddd.repr)}
    )
    ax = plt.subplot(gs[:3, :-1])
    ax.axis("off")
    for lineno, indicators in enumerate(INDICATORS):
        for index_in_line, i in enumerate(indicators):
            x = INDICATOR_X_POS[index_in_line]
            y = INDICATOR_Y_POS[lineno]
            ax.text(x, y.label, _(i.label), color=i.color, fontsize=label_font_size),
            ax.text(x, y.value, indicator_values[i.key], color=BLACK, fontsize=i.value_font_size)

    # strategy vs benchmark
    ax = plt.subplot(gs[4:10, :])
    ax.get_xaxis().set_minor_locator(ticker.AutoMinorLocator())
    ax.get_yaxis().set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(b=True, which='minor', linewidth=.2)
    ax.grid(b=True, which='major', linewidth=1)

    # plot two lines
    ax.plot(portfolio["unit_net_value"] - 1.0, label=_(u"strategy"), alpha=1, linewidth=2, color=RED)
    if benchmark_portfolio is not None:
        ax.plot(benchmark_portfolio["unit_net_value"] - 1.0, label=_(u"benchmark"), alpha=1, linewidth=2, color=BLUE)

    # plot MaxDD/MaxDDD
    rt = portfolio.unit_net_value.values
    max_dd.plot(ax, rt, "v", "Green", _("MaxDrawdown"))
    max_ddd.plot(ax, rt, "D", "Blue", _("MaxDDD"))

    # place legend
    leg = plt.legend(loc="best")
    leg.get_frame().set_alpha(0.5)

    # manipulate axis
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:3.2f}%'.format(x * 100) for x in vals])

    # plot user plots
    if "plots" in result_dict:
        plots_df = result_dict["plots"]

        ax2 = plt.subplot(gs[11:, :])
        for column in plots_df.columns:
            ax2.plot(plots_df[column], label=column)

        leg = plt.legend(loc="best")
        leg.get_frame().set_alpha(0.5)

    # logo as watermark
    fig.figimage(
        logo_img,
        xo=((img_width * dpi) - logo_img.shape[1]) / 2,
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
