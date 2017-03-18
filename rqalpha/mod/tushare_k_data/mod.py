from rqalpha.interface import AbstractMod

from .data_source import TushareKDataSource


class TushareKDataMode(AbstractMod):
    def __init__(self):
        pass

    def start_up(self, env, mod_config):
        env.set_data_source(TushareKDataSource(env.config.base.data_bundle_path))

    def tear_down(self, code, exception=None):
        pass
