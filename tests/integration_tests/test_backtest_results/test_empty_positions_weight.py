# -*- coding: utf-8 -*-
from rqalpha import run_func


def init(context):
    pass


def handle_bar(context, bar_dict):
    pass


def test_empty_positions_weight_dtype(bundle_path):
    config = {
        "base": {
            "start_date": "2020-01-02",
            "end_date": "2020-01-08",
            "frequency": "1d",
            "data_bundle_path": bundle_path,
            "accounts": {"stock": 100000},
        },
        "extra": {"log_level": "error"},
    }

    result = run_func(config=config, init=init, handle_bar=handle_bar)
    positions_weight = result["sys_analyser"]["positions_weight"]

    assert not positions_weight.empty
    assert positions_weight.index.equals(result["sys_analyser"]["portfolio"].index)
    assert set(positions_weight.dtypes.astype(str)) == {"float64"}
    assert (positions_weight.to_numpy() == 0).all()
