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

import codecs

from ..interface import AbstractStrategyLoader
from ..utils.strategy_loader_help import compile_strategy


class FileStrategyLoader(AbstractStrategyLoader):
    def load(self, strategy, scope):
        with codecs.open(strategy, encoding="utf-8") as f:
            source_code = f.read()

        return compile_strategy(source_code, strategy, scope)


class SourceCodeStrategyLoader(AbstractStrategyLoader):
    def load(self, strategy, scope):
        return compile_strategy(strategy, "strategy.py", scope)
