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

import copy
from collections import OrderedDict

from rqalpha.utils.package_helper import import_mod
from rqalpha.utils.logger import system_log, basic_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils import RqAttrDict


class ModHandler(object):
    def __init__(self):
        self._env = None
        self._mod_list = list()
        self._mod_dict = OrderedDict()

    def set_env(self, environment):
        self._env = environment

        config = environment.config

        for mod_name in config.mod.__dict__:
            mod_config = getattr(config.mod, mod_name)
            if not mod_config.enabled:
                continue
            self._mod_list.append((mod_name, mod_config))

        for idx, (mod_name, user_mod_config) in enumerate(self._mod_list):
            if hasattr(user_mod_config, 'lib'):
                lib_name = user_mod_config.lib
            elif mod_name in SYSTEM_MOD_LIST:
                lib_name = "rqalpha.mod.rqalpha_mod_" + mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            system_log.debug(_(u"loading mod {}").format(lib_name))
            mod_module = import_mod(lib_name)
            if mod_module is None:
                del self._mod_list[idx]
                return
            mod = mod_module.load_mod()

            mod_config = RqAttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))
            mod_config.update(user_mod_config)
            setattr(config.mod, mod_name, mod_config)
            self._mod_list[idx] = (mod_name, mod_config)
            self._mod_dict[mod_name] = mod

        self._mod_list.sort(key=lambda item: getattr(item[1], "priority", 100))
        environment.mod_dict = self._mod_dict

    def start_up(self):
        for mod_name, mod_config in self._mod_list:
            basic_system_log.debug(_(u"mod start_up [START] {}").format(mod_name))
            self._mod_dict[mod_name].start_up(self._env, mod_config)
            basic_system_log.debug(_(u"mod start_up [END]   {}").format(mod_name))

    def tear_down(self, *args):
        result = {}
        for mod_name, __ in reversed(self._mod_list):
            try:
                basic_system_log.debug(_(u"mod tear_down [START] {}").format(mod_name))
                ret = self._mod_dict[mod_name].tear_down(*args)
                basic_system_log.debug(_(u"mod tear_down [END]   {}").format(mod_name))
            except Exception as e:
                system_log.exception("tear down fail for {}", mod_name)
                continue
            if ret is not None:
                result[mod_name] = ret
        return result


SYSTEM_MOD_LIST = [
    "sys_accounts",
    "sys_analyser",
    "sys_progress",
    "sys_funcat",
    "sys_risk",
    "sys_simulation",
    "sys_stock_realtime",
]
