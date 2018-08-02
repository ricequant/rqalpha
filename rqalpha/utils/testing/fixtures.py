import os
from contextlib import contextmanager

from unittest.mock import MagicMock


class EnvironmentFixture(object):
    def __init__(self, *args, **kwargs):
        super(EnvironmentFixture, self).__init__(*args, **kwargs)
        self.env = None

    def init_fixture(self):
        super(EnvironmentFixture, self).init_fixture()
        from rqalpha.environment import Environment
        self.env = Environment({})

    @contextmanager
    def mock_env_get_last_price(self, *args, **kwargs):
        origin_get_last_price = self.env.get_last_price
        self.env.get_last_price = MagicMock(*args, **kwargs)
        yield
        self.env.get_last_price = origin_get_last_price


class BaseDataSourceFixture(object):
    def __init__(self, *args, **kwargs):
        super(BaseDataSourceFixture, self).__init__(*args, **kwargs)
        self.base_data_source = None

    def init_fixture(self):
        super(BaseDataSourceFixture, self).init_fixture()
        from rqalpha.data.base_data_source import BaseDataSource
        # TODO: use mocked bcolz file
        self.base_data_source = BaseDataSource(os.path.abspath(os.path.expanduser('~/.rqalpha/bundle')))

