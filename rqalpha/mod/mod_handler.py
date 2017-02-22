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

from importlib import import_module
from collections import OrderedDict

from rqalpha.utils.logger import system_log


class ModHandler(object):
    def __init__(self):
        self._env = None
        self._mod_list = []
        self._mod_dict = OrderedDict()

    def set_env(self, environment):
        self._env = environment

        config = environment.config

        for mod_name in config.mod.__dict__:
            mod_config = getattr(config.mod, mod_name)
            if not mod_config.enabled:
                continue
            self._mod_list.append((mod_name, mod_config))

        self._mod_list.sort(key=lambda item: item[1].priority)
        for mod_name, mod_config in self._mod_list:
            system_log.debug('loading mod {}', mod_name)
            mod_module = import_module(mod_config.lib)
            mod = mod_module.load_mod()
            self._mod_dict[mod_name] = mod

        environment.mod_dict = self._mod_dict

    def start_up(self):
        for mod_name, mod_config in self._mod_list:
            self._mod_dict[mod_name].start_up(self._env, mod_config)

    def tear_down(self, *args):
        for mod_name, _ in reversed(self._mod_list):
            self._mod_dict[mod_name].tear_down(*args)
