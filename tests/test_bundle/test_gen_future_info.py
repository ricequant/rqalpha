# -*- coding: utf-8 -*-
import json
import warnings
from types import SimpleNamespace

import pandas as pd

from rqalpha.data import bundle

LEGACY_FUTURE_INFO = [
    {
        "underlying_symbol": "A",
        "close_commission_ratio": 1.0,
        "close_commission_today_ratio": 0.0,
        "commission_type": "by_volume",
        "open_commission_ratio": 1.0,
        "tick_size": 1.0,
    }
]


class FakeRQDatac:
    def __init__(self):
        # get_dominant 返回以日期为索引的 Series，正是 [-1] 出错的形态
        self.dominant = pd.Series(["A2001.XDCE"], index=pd.to_datetime(["2020-01-02"]))

    def all_instruments(self, type=None):
        return pd.DataFrame({"order_book_id": ["A2001.XDCE"], "margin_rate": [0.07]})

    def instruments(self, order_book_id):
        return SimpleNamespace(margin_rate=0.07, tick_size=lambda: 1.0)

    @property
    def futures(self):
        return SimpleNamespace(
            get_dominant=lambda underlying_symbol: self.dominant,
            get_commission_margin=lambda: pd.DataFrame({
                "order_book_id": ["A2001.XDCE"],
                "close_commission_ratio": [1.0],
                "close_commission_today_ratio": [0.0],
                "commission_type": ["by_volume"],
                "open_commission_ratio": [1.0],
            }),
        )


def test_migrate_legacy_future_info_margin_rate(tmp_path, monkeypatch):
    future_info_file = tmp_path / "future_info.json"
    future_info_file.write_text(json.dumps(LEGACY_FUTURE_INFO))

    monkeypatch.setattr(bundle, "rqdatac", FakeRQDatac())

    with warnings.catch_warnings():
        # pandas 2 对 Series[整数] 发这条警告，pandas 3 直接 KeyError(-1)
        warnings.filterwarnings("error", message=".*treating keys as positions.*")
        bundle.gen_future_info(str(tmp_path))

    migrated = [i for i in json.loads(future_info_file.read_text()) if i.get("underlying_symbol") == "A"]
    assert migrated and migrated[0]["margin_rate"] == 0.07
