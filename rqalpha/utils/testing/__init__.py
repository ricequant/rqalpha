from unittest import TestCase

from .mock import mock_instrument
from .fixtures import (
    EnvironmentFixture,
    BaseDataSourceFixture
)


class RQAlphaTestCase(TestCase):
    def init_fixture(self):
        pass

    def setUp(self):
        self.init_fixture()


__all__ = [
    "RQAlphaTestCase",
    "EnvironmentFixture",
    "BaseDataSourceFixture",
    "mock_instrument"
]
