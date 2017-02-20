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

from ..interface import AbstractPersistProvider


class DiskPersistProvider(AbstractPersistProvider):
    def __init__(self, path="./persist"):
        self._path = path
        try:
            os.makedirs(self._path)
        except:
            pass

    def store(self, key, value):
        assert isinstance(value, bytes), "value must be bytes"
        with open(os.path.join(self._path, key), "wb") as f:
            f.write(value)

    def load(self, key, large_file=False):
        try:
            with open(os.path.join(self._path, key), "rb") as f:
                return f.read()
        except IOError as e:
            return None
