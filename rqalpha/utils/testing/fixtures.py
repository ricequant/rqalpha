import os
import pickle
from contextlib import contextmanager

from unittest.mock import MagicMock

import six


class EnvironmentFixture(object):
    def __init__(self, *args, **kwargs):
        super(EnvironmentFixture, self).__init__(*args, **kwargs)
        self.env = None

    def init_fixture(self):
        from rqalpha.environment import Environment

        super(EnvironmentFixture, self).init_fixture()
        self.env = Environment({})

    @contextmanager
    def mock_env_get_last_price(self, *args, **kwargs):
        origin_get_last_price = self.env.get_last_price
        self.env.get_last_price = MagicMock(*args, **kwargs)
        yield
        self.env.get_last_price = origin_get_last_price


class TempDirFixture(object):
    def __init__(self, *args, **kwargs):
        super(TempDirFixture, self).__init__(*args, **kwargs)
        self.temp_dir = None

    def init_fixture(self):
        from tempfile import TemporaryDirectory

        super(TempDirFixture, self).init_fixture()
        self.temp_dir = TemporaryDirectory()


class BaseDataSourceFixture(TempDirFixture):
    def __init__(self, *args, **kwargs):
        super(BaseDataSourceFixture, self).__init__(*args, **kwargs)

        self._bcolz_data = {key: None for key in [
            "stocks", "indexes", "futures", "funds", "original_dividends", "trading_dates",
            "yield_curve", "split_factor", "ex_cum_factor", "st_stock_days", "suspended_days"
        ]}
        self._pk_data = {"instruments": None}

        self.base_data_source = None

    def init_fixture(self):
        from rqalpha.data.base_data_source import BaseDataSource

        super(BaseDataSourceFixture, self).init_fixture()
        default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))

        for key, table in six.iteritems(self._bcolz_data):
            table_relative_path = "{}.bcolz".format(key)
            if table is None:
                os.symlink(
                    os.path.join(default_bundle_path, table_relative_path),
                    os.path.join(self.temp_dir.name, table_relative_path)
                )
            else:
                table.rootdir = os.path.join(self.temp_dir.name, "{}.bcolz".format(key))
                table.flush()

        for key, obj in six.iteritems(self._pk_data):
            pickle_raletive_path = "{}.pk".format(key)
            if obj is None:
                os.symlink(
                    os.path.join(default_bundle_path, pickle_raletive_path),
                    os.path.join(self.temp_dir.name, pickle_raletive_path)
                )
            else:
                with open(os.path.join(self.temp_dir.name, "{}.pk".format(key)), "wb+") as out:
                    pickle.dump(obj, out, protocol=2)

        # TODO: use mocked bcolz file
        self.base_data_source = BaseDataSource(self.temp_dir.name)
