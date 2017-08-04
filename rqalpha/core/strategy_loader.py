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

import re
import codecs

from ..interface import AbstractStrategyLoader
from ..utils.strategy_loader_help import compile_strategy

ENCODING_RE = re.compile("#.*coding[:=]\s*([-\w.]+)")


class FileStrategyLoader(AbstractStrategyLoader):
    def __init__(self, strategy_file_path):
        self._strategy_file_path = strategy_file_path

    def load(self, scope):
        with codecs.open(self._strategy_file_path, encoding="utf-8") as f:
            raw_first_line = f.readline()
            raw_second_line = f.readline()
            # a little bit tricky, ensure track of stack refer to the right line.
            first_line = "" if ENCODING_RE.match(
                raw_first_line) else raw_first_line  # for shell comment, ex: #!/bin/bash
            second_line = "" if ENCODING_RE.match(
                raw_second_line) else raw_second_line  # for encoding comment, ex: # coding: utf-8
            source_code = "\n".join([first_line, second_line, f.read()])

        return compile_strategy(source_code, self._strategy_file_path, scope)


class SourceCodeStrategyLoader(AbstractStrategyLoader):
    def __init__(self, code):
        self._code = code

    def load(self, scope):
        return compile_strategy(self._code, "strategy.py", scope)


class UserFuncStrategyLoader(AbstractStrategyLoader):
    def __init__(self, user_funcs):
        self._user_funcs = user_funcs

    def load(self, scope):
        return self._user_funcs
