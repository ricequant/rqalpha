from unittest import TestCase

from .mocking import mock_instrument, mock_bar, mock_tick
from .fixtures import (
    MagicMock,
    RQAlphaFixture,
    EnvironmentFixture,
    UniverseFixture,
    DataProxyFixture,
    BaseDataSourceFixture,
    BarDictPriceBoardFixture,
    MatcherFixture,
)


class RQAlphaTestCase(TestCase):
    def init_fixture(self):
        pass

    def assertObj(self, obj, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict) and not isinstance(getattr(obj, k), dict):
                self.assertObj(getattr(obj, k), **v)
            else:
                self.assertEqual(getattr(obj, k), v)

    def setUp(self):
        self.init_fixture()


__all__ = [
    "MagicMock",
    "RQAlphaFixture",
    "RQAlphaTestCase",
    "EnvironmentFixture",
    "UniverseFixture",
    "DataProxyFixture",
    "BaseDataSourceFixture",
    "BarDictPriceBoardFixture",
    "MatcherFixture",
    "mock_instrument",
    "mock_bar",
    "mock_tick"
]
