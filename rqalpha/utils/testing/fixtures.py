import os
import pickle
from contextlib import contextmanager

import six

if six.PY3:
    from unittest.mock import MagicMock
else:
    from mock import MagicMock


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
    def mock_env_method(self, name, mock_method):
        origin_method = getattr(self.env, name)
        setattr(self.env, name, mock_method)
        yield
        setattr(self.env, name, origin_method)

    @contextmanager
    def mock_env_get_last_price(self, *args, **kwargs):
        origin_get_last_price = self.env.get_last_price
        self.env.get_last_price = MagicMock(*args, **kwargs)
        yield
        self.env.get_last_price = origin_get_last_price


class UniverseFixture(EnvironmentFixture):
    def init_fixture(self):
        from rqalpha.core.strategy_universe import StrategyUniverse

        super(UniverseFixture, self).init_fixture()
        self.env._universe = StrategyUniverse()


class TempDirFixture(RQAlphaFixture):
    def __init__(self, *args, **kwargs):
        super(TempDirFixture, self).__init__(*args, **kwargs)
        self.temp_dir = None

    def init_fixture(self):
        if six.PY3:
            from tempfile import TemporaryDirectory
        else:
            from backports.tempfile import TemporaryDirectory

        super(TempDirFixture, self).init_fixture()
        self.temp_dir = TemporaryDirectory()


class BaseDataSourceFixture(TempDirFixture, EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BaseDataSourceFixture, self).__init__(*args, **kwargs)

        from rqalpha.const import MARKET

        self.env_config = {
            "base": {
                "market": MARKET.CN,
                "accounts": {"STOCK": 100}
            }
        }

        self.base_data_source = None

    def init_fixture(self):
        from rqalpha.data.base_data_source import BaseDataSource

        super(BaseDataSourceFixture, self).init_fixture()
        default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))
        self.base_data_source = BaseDataSource(default_bundle_path, {})


class BarDictPriceBoardFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BarDictPriceBoardFixture, self).__init__(*args, **kwargs)
        self.price_board = None

    def init_fixture(self):
        from rqalpha.data.bar_dict_price_board import BarDictPriceBoard

        super(BarDictPriceBoardFixture, self).init_fixture()

        self.price_board = BarDictPriceBoard()
        self.env.set_price_board(self.price_board)


class DataProxyFixture(BaseDataSourceFixture, BarDictPriceBoardFixture):
    def __init__(self, *args, **kwargs):
        super(DataProxyFixture, self).__init__(*args, **kwargs)
        self.data_proxy = None
        self.data_source = None

    def init_fixture(self):
        from rqalpha.data.data_proxy import DataProxy

        super(DataProxyFixture, self).init_fixture()
        if not self.data_source:
            self.data_source = self.base_data_source
        self.data_proxy = DataProxy(self.data_source, self.price_board)
        self.env.set_data_proxy(self.data_proxy)
        try:
            self.env.config.base.trading_calendar = self.data_proxy.get_trading_dates(
                self.env.config.base.start_date, self.env.config.base.end_date
            )
        except AttributeError:
            pass

    @contextmanager
    def mock_data_proxy_method(self, name, mock_method):
        origin_method = getattr(self.env.data_proxy, name)
        setattr(self.env.data_proxy, name, mock_method)
        yield
        setattr(self.env.data_proxy, name, origin_method)


class MatcherFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(MatcherFixture, self).__init__(*args, **kwargs)

        from rqalpha.mod.rqalpha_mod_sys_simulation import __config__ as mod_sys_simulation_config
        from rqalpha.const import MATCHING_TYPE

        self.env_config = {
            "mod": {
                "sys_simulation": mod_sys_simulation_config
            }
        }

        self.env_config["mod"]["sys_simulation"]["matching_type"] = MATCHING_TYPE.CURRENT_BAR_CLOSE

        self.matcher = None

    def init_fixture(self):
        from datetime import datetime
        from rqalpha.mod.rqalpha_mod_sys_simulation.matcher import DefaultMatcher
        
        super(MatcherFixture, self).init_fixture()

        print(DefaultMatcher, type(self.env_config["mod"]))

        self.matcher = DefaultMatcher(self.env, self.env_config["mod"].sys_simulation)
        self.matcher.update(datetime(2018, 8, 16, 11, 5), datetime(2018, 8, 16, 11, 5))
