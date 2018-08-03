import os
import pickle
from contextlib import contextmanager

from unittest.mock import MagicMock

import six


class RQAlphaFixture(object):
    def init_fixture(self):
        pass


class EnvironmentFixture(RQAlphaFixture):
    def __init__(self, *args, **kwargs):
        super(EnvironmentFixture, self).__init__(*args, **kwargs)
        self.env_config = {}
        self.env = None

    def init_fixture(self):
        from rqalpha.utils import RqAttrDict
        from rqalpha.environment import Environment

        super(EnvironmentFixture, self).init_fixture()
        self.env = Environment(RqAttrDict(self.env_config))

    @contextmanager
    def mock_env_get_last_price(self, *args, **kwargs):
        origin_get_last_price = self.env.get_last_price
        self.env.get_last_price = MagicMock(*args, **kwargs)
        yield
        self.env.get_last_price = origin_get_last_price


class TempDirFixture(RQAlphaFixture):
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

        self.bcolz_data = {key: None for key in [
            "stocks", "indexes", "futures", "funds", "original_dividends", "trading_dates",
            "yield_curve", "split_factor", "ex_cum_factor", "st_stock_days", "suspended_days"
        ]}
        self.pk_data = {"instruments": None}

        self.base_data_source = None

    def init_fixture(self):
        from rqalpha.data.base_data_source import BaseDataSource

        super(BaseDataSourceFixture, self).init_fixture()
        default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))

        for key, table in six.iteritems(self.bcolz_data):
            table_relative_path = "{}.bcolz".format(key)
            if table is None:
                os.symlink(
                    os.path.join(default_bundle_path, table_relative_path),
                    os.path.join(self.temp_dir.name, table_relative_path)
                )
            else:
                table.rootdir = os.path.join(self.temp_dir.name, "{}.bcolz".format(key))
                table.flush()

        for key, obj in six.iteritems(self.pk_data):
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


class BenchmarkAccountFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BenchmarkAccountFixture, self).__init__(*args, **kwargs)

        self.benchmark_account_total_cash = 4000
        self.benchmark_account = None

    def init_fixture(self):
        from rqalpha.model.base_position import Positions
        from rqalpha.mod.rqalpha_mod_sys_accounts.position_model.stock_position import StockPosition
        from rqalpha.mod.rqalpha_mod_sys_accounts.account_model import BenchmarkAccount

        super(BenchmarkAccountFixture, self).init_fixture()

        self.benchmark_account = BenchmarkAccount(self.benchmark_account_total_cash,  Positions(StockPosition))
