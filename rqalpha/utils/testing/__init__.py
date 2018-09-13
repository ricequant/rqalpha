from unittest import TestCase

from .mock import mock_instrument, mock_bar, mock_tick
from .fixtures import (
    RQAlphaFixture,
    EnvironmentFixture,
    BaseDataSourceFixture,
    BarDictPriceBoardFixture,
    MatcherFixture,
    BookingFixture,
)


class RQAlphaTestCase(TestCase):
    def init_fixture(self):
        pass

    def setUp(self):
        self.init_fixture()


__all__ = [
    "RQAlphaFixture",
    "RQAlphaTestCase",
    "EnvironmentFixture",
    "BaseDataSourceFixture",
    "BarDictPriceBoardFixture",
    "MatcherFixture",
    "BookingFixture",
    "mock_instrument",
    "mock_bar",
    "mock_tick"
]
