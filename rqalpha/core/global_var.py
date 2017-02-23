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

import six
import pickle
from ..utils.logger import user_system_log, system_log, user_detail_log


class GlobalVars(object):
    def get_state(self):
        dict_data = {}
        for key, value in six.iteritems(self.__dict__):
            try:
                dict_data[key] = pickle.dumps(value)
            except Exception as e:
                user_detail_log.exception("g.{} can not pickle", key)
                user_system_log.warn("g.{} can not pickle", key)
        return pickle.dumps(dict_data)

    def set_state(self, state):
        dict_data = pickle.loads(state)
        for key, value in six.iteritems(dict_data):
            try:
                self.__dict__[key] = pickle.loads(value)
                system_log.debug("restore g.{} {}", key, type(self.__dict__[key]))
            except Exception as e:
                user_detail_log.exception("g.{} can not restore", key)
                user_system_log.warn("g.{} can not restore", key)
