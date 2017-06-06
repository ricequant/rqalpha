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

import os
import pandas as pd
from rqalpha.interface import AbstractMod


__config__ = {
    "csv_path": None
}


def load_mod():
    return ExtendAPIDemoMod()


class ExtendAPIDemoMod(AbstractMod):
    def __init__(self):
        # 注入API 一定要在初始化阶段，否则无法成功注入
        self._csv_path = None
        self._inject_api()

    def start_up(self, env, mod_config):
        self._csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), mod_config.csv_path))

    def tear_down(self, code, exception=None):
        pass

    def _inject_api(self):
        from rqalpha import export_as_api
        from rqalpha.execution_context import ExecutionContext
        from rqalpha.const import EXECUTION_PHASE

        @export_as_api
        @ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                        EXECUTION_PHASE.BEFORE_TRADING,
                                        EXECUTION_PHASE.ON_BAR,
                                        EXECUTION_PHASE.AFTER_TRADING,
                                        EXECUTION_PHASE.SCHEDULED)
        def get_csv_as_df():
            data = pd.read_csv(self._csv_path)
            return data
