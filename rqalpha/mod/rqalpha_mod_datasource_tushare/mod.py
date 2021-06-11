#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: jaxon
@Time: 2021-03-27 23:40
"""

from rqalpha.interface import AbstractMod
from .data_source import TushareKDataSource


class TushareKDataMode(AbstractMod):
    def __init__(self):
        pass

    def start_up(self, env, mod_config):
        # 设置 data_source 为 TushareKDataSource 类的对象
        env.set_data_source(TushareKDataSource(env.config.base.data_bundle_path))

    def tear_down(self, code, exception=None):
        pass