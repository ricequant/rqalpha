#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Hua Liang[Stupid ET] <et@everet.org>
#

from rqalpha.interface import AbstractMod
from rqalpha.utils.logger import system_log

from .data_source import DataSource
from .event_source import RealtimeEventSource


class RealtimeTradeMod(AbstractMod):

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

        env.set_data_source(DataSource(env.config.base.data_bundle_path))
        env.set_event_source(RealtimeEventSource())

    def tear_down(self, code, exception=None):
        pass
