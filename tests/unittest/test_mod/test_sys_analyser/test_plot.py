from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from rqalpha.mod.rqalpha_mod_sys_analyser.plot import plot
from rqalpha.mod.rqalpha_mod_sys_analyser.plot.consts import CLOSE_POINT, OPEN_POINT
from rqalpha.mod.rqalpha_mod_sys_analyser.plot.utils import IndexRange


@pytest.mark.parametrize("string_storage", ["python", "pyarrow"])
def test_open_close_points_with_string_storage(monkeypatch, string_storage):
    if string_storage == "pyarrow":
        pytest.importorskip("pyarrow")

    dates = pd.to_datetime(["2026-01-05", "2026-01-06"])
    trades = pd.DataFrame({
        "position_effect": pd.Series(["OPEN", "CLOSE"], dtype=pd.StringDtype(storage=string_storage)),
        "trading_datetime": pd.to_datetime(["2026-01-05 10:00", "2026-01-06 10:00"]),
    })
    assert trades.position_effect.dtype.storage == string_storage
    if string_storage == "python":
        assert isinstance(trades.position_effect.array, pd.arrays.StringArray)

    result = {
        "portfolio": pd.DataFrame({"unit_net_value": [1.0, 1.1]}, index=dates),
        "trades": trades,
        "summary": {
            "strategy_file": "strategy.py",
            "max_drawdown_duration": IndexRange.new(0, 1, dates),
        },
    }
    render = Mock()
    monkeypatch.setattr(plot, "_plot", render)

    plot.plot_result(result, show=False, open_close_points=True)

    render.assert_called_once()
    sub_plots = render.call_args.args[1]
    return_plot = next(sub_plot for sub_plot in sub_plots if isinstance(sub_plot, plot.ReturnPlot))
    spots = {info: positions for positions, info in return_plot._spots_on_returns}
    np.testing.assert_array_equal(spots[OPEN_POINT], [0])
    np.testing.assert_array_equal(spots[CLOSE_POINT], [1])
