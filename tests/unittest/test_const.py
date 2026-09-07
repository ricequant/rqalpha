import pytest

from rqalpha.const import MARKET


@pytest.mark.parametrize(
    "value, expected",
    [
        ("CN", MARKET.CN),
        ("cn", MARKET.CN),
        ("Cn", MARKET.CN),
        ("HK", MARKET.HK),
        ("hk", MARKET.HK),
        ("Hk", MARKET.HK),
    ],
)
def test_market_accepts_case_insensitive_values(value, expected):
    assert MARKET(value) is expected


@pytest.mark.parametrize(
    "key, expected",
    [
        ("CN", MARKET.CN),
        ("cn", MARKET.CN),
        ("HK", MARKET.HK),
        ("hk", MARKET.HK),
    ],
)
def test_market_accepts_case_insensitive_keys(key, expected):
    assert MARKET[key] is expected
