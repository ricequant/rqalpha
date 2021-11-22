from typing import NamedTuple

import numpy as np
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.layouts import layout
from bokeh.models import DatetimeTickFormatter, NumeralTickFormatter, BoxAnnotation
from bokeh.core.enums import RenderLevel

from rqalpha.utils.i18n import gettext as _
from rqalpha.mod.rqalpha_mod_sys_analyser.plot import _max_ddd


class Colors:
    STRATEGY_LINE = "#aa4643"
    BENCHMARK_LINE = "#5193ff"
    MAX_DD_BOX = "#90EE90"
    MAX_DDD_BOX = "#00FFFF"


class IndexRange(NamedTuple):
    start: int
    end: int

    def date_repr(self, index):
        return "{}~{}, {} days".format(index[self.start], index[self.end], (index[self.end] - index[self.start]).days)


def plot_result(result_dict, show_windows=True, savefile=None):
    p = Plot(result_dict["portfolio"], result_dict["benchmark_portfolio"], result_dict["summary"])
    p.plot()
    if show_windows:
        p.show()


class Plot:
    def __init__(self, portfolio: pd.DataFrame, benchmark_portfolio: pd.DataFrame, summary):
        self._p = portfolio
        self._bp = benchmark_portfolio
        self._s = summary
        self._fig = figure(x_axis_type="datetime")
        self._fig.xaxis.formatter = DatetimeTickFormatter(months='%Y-%m')
        self._fig.yaxis.formatter = NumeralTickFormatter(format="0.00%")
        self._divs = []

    def plot(self):
        self._plot_line(self._p.index, self._p.unit_net_value - 1.0, Colors.STRATEGY_LINE, _("Strategy Returns"))
        self._plot_line(self._bp.index, self._bp.unit_net_value - 1.0, Colors.BENCHMARK_LINE, _("Benchmark Returns"))
        portfolio_value = self._p.unit_net_value * self._p.units
        max_dd = _max_dd(portfolio_value.values)
        max_ddd = _max_ddd(portfolio_value.values, portfolio_value.index)
        self._plot_box(*max_dd, Colors.MAX_DD_BOX, _("MaxDD"))
        self._plot_box(max_ddd.start, max_ddd.end, Colors.MAX_DDD_BOX, _("MaxDDD"))
        self._fig.legend.location = "bottom_right"

    def show(self):
        show(layout(self._divs + [
            [self._fig]
        ], sizing_mode="stretch_width"))

    def _plot_line(self, x, y, color, label):
        self._fig.line(x, y, line_width=2, color=color, legend_label=label)

    def _plot_box(self, start, end, color, label, alpha=0.5):
        index = self._p.index
        self._fig.add_layout(BoxAnnotation(
            left=index[start], right=index[end], fill_color=color, fill_alpha=alpha, level=RenderLevel.image
        ))
        # legend
        self._fig.quad(top=[0], bottom=[0], left=[index[start]], right=[index[start]], color=color, legend_label=label)


def _max_dd(arr) -> IndexRange:
    end = np.argmax(np.maximum.accumulate(arr) / arr)
    if end == 0:
        end = len(arr) - 1
    start = np.argmax(arr[:end]) if end > 0 else 0
    return IndexRange(start, end)


if __name__ == "__main__":
    import pickle
    with open("result.pkl", "rb") as f:
        plot_result(pickle.loads(f.read()))
