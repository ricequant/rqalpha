from datetime import date

import numpy as np

from rqalpha.data.base_data_source.data_source import BaseDataSource


def test_open_auction_bar_does_not_copy_day_liquidity():
    bar_dtype = np.dtype(
        [
            ("datetime", "u8"),
            ("open", "f8"),
            ("limit_up", "f8"),
            ("limit_down", "f8"),
            ("volume", "f8"),
            ("total_turnover", "f8"),
        ]
    )
    full_day_bar = np.array(
        (20260908, 10.5, 11.5, 9.5, 123456.0, 789012.0), dtype=bar_dtype
    )

    class StubDataSource:
        OPEN_AUCTION_BAR_FIELDS = BaseDataSource.OPEN_AUCTION_BAR_FIELDS
        get_open_auction_bar = BaseDataSource.get_open_auction_bar

        def get_bar(self, instrument, dt, frequency):
            assert frequency == "1d"
            return full_day_bar

    auction_bar = BaseDataSource.get_open_auction_bar(
        StubDataSource(), "000001.XSHE", date(2026, 9, 8)
    )

    assert auction_bar["open"] == full_day_bar["open"]
    assert auction_bar["limit_up"] == full_day_bar["limit_up"]
    assert auction_bar["limit_down"] == full_day_bar["limit_down"]
    assert np.isnan(auction_bar["volume"])
    assert np.isnan(auction_bar["total_turnover"])

    assert np.isnan(
        BaseDataSource.get_open_auction_volume(
            StubDataSource(), "000001.XSHE", date(2026, 9, 8)
        )
    )

    class AuctionVolumeOverride(StubDataSource):
        def get_open_auction_bar(self, instrument, dt):
            return {"volume": 321.0}

    assert BaseDataSource.get_open_auction_volume(
        AuctionVolumeOverride(), "000001.XSHE", date(2026, 9, 8)
    ) == 321.0

    class MissingAuctionBar(StubDataSource):
        def get_open_auction_bar(self, instrument, dt):
            return None

    assert np.isnan(
        BaseDataSource.get_open_auction_volume(
            MissingAuctionBar(), "000001.XSHE", date(2026, 9, 8)
        )
    )
