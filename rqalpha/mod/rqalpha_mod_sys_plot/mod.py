# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click

from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT


class PlotMod(AbstractMod):
    def __init__(self):
        self._env = None

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config

    def tear_down(self, success, exception=None):
        env = self._env
        # FIXME need a better way to access data from other mod
        if 'sys_analyser' in env.mod_dict:
            result_dict = env.mod_dict['sys_analyser']._result

            if self._mod_config.plot:
                from .plot import plot_result
                plot_result(result_dict)

            if self._mod_config.plot_save_file:
                from .plot import plot_result
                plot_result(result_dict, False, self._mod_config.plot_save_file)
