import pandas as pd

from rqalpha.const import SIDE
from rqalpha.utils.price_limits import (
    PRICE_LIMIT_TOLERANCE,
    reaches_limit,
    reaches_limit_down,
    reaches_limit_down_vectorized,
    reaches_limit_up,
    reaches_limit_up_vectorized,
)


class _MockPriceBoard:
    def __init__(self, limit_up=10.0, limit_down=9.0):
        self._limit_up = limit_up
        self._limit_down = limit_down

    def get_limit_up(self, order_book_id):
        return self._limit_up

    def get_limit_down(self, order_book_id):
        return self._limit_down


def test_reaches_limit_up_uses_last_tick_band():
    assert not reaches_limit_up(10.0 - 0.01, 10.0, 0.01)
    assert reaches_limit_up(10.0 - 0.01 + PRICE_LIMIT_TOLERANCE, 10.0, 0.01)


def test_reaches_limit_down_uses_last_tick_band():
    assert not reaches_limit_down(9.0 + 0.01, 9.0, 0.01)
    assert reaches_limit_down(9.0 + 0.01 - PRICE_LIMIT_TOLERANCE, 9.0, 0.01)


def test_reaches_limit_dispatches_by_side():
    price_board = _MockPriceBoard()

    assert reaches_limit("000001.XSHE", 9.990001, SIDE.BUY, price_board, 0.01)
    assert reaches_limit("000001.XSHE", 9.009999, SIDE.SELL, price_board, 0.01)


def test_vectorized_limit_helpers_match_scalar_behavior():
    prices = pd.Series(
        [9.99, 9.990001, 9.01, 9.009999, 9.5],
        index=["buy_ok", "buy_hit", "sell_ok", "sell_hit", "mid"],
        dtype=float,
    )
    limit_up = pd.Series(10.0, index=prices.index, dtype=float)
    limit_down = pd.Series(9.0, index=prices.index, dtype=float)
    tick_sizes = pd.Series(0.01, index=prices.index, dtype=float)

    assert reaches_limit_up_vectorized(prices, limit_up, tick_sizes).to_dict() == {
        "buy_ok": False,
        "buy_hit": True,
        "sell_ok": False,
        "sell_hit": False,
        "mid": False,
    }
    assert reaches_limit_down_vectorized(prices, limit_down, tick_sizes).to_dict() == {
        "buy_ok": False,
        "buy_hit": False,
        "sell_ok": False,
        "sell_hit": True,
        "mid": False,
    }
