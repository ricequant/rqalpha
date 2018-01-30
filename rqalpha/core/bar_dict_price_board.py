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

import numpy as np

from rqalpha.interface import AbstractPriceBoard
from rqalpha.environment import Environment


class BarDictPriceBoard(AbstractPriceBoard):
    def __init__(self):
        self._env = Environment.get_instance()

    @property
    def _bar_dict(self):
        return self._env.bar_dict

    def get_last_price(self, order_book_id):
        return np.nan if self._bar_dict.dt is None else self._bar_dict[order_book_id].last

    def get_limit_up(self, order_book_id):
        return np.nan if self._bar_dict.dt is None else self._bar_dict[order_book_id].limit_up

    def get_limit_down(self, order_book_id):
        return np.nan if self._bar_dict.dt is None else self._bar_dict[order_book_id].limit_down

    def get_a1(self, order_book_id):
        return np.nan

    def get_b1(self, order_book_id):
        return np.nan
