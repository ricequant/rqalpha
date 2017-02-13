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

from collections import namedtuple

import numpy as np

Rule = namedtuple('Rule', ['dtype', 'multiplier', 'round'])


class Converter(object):
    def __init__(self, rules):
        self._rules = rules

    def convert(self, name, data):
        try:
            r = self._rules[name]
        except KeyError:
            return data

        result = data * r.multiplier
        if r.round:
            result = np.round(result, r.round)

        return result

    def field_type(self, name, dt):
        try:
            return self._rules[name].dtype
        except KeyError:
            return dt

float64 = np.dtype('float64')

StockBarConverter = Converter({
    'open': Rule(float64, 1 / 10000.0, 4),
    'close': Rule(float64, 1 / 10000.0, 4),
    'high': Rule(float64, 1 / 10000.0, 4),
    'low': Rule(float64, 1 / 10000.0, 4),
    'limit_up': Rule(float64, 1/10000.0, 4),
    'limit_down': Rule(float64, 1/10000.0, 4),
})

FutureDayBarConverter = Converter({
    'open': Rule(float64, 1 / 10000.0, 2),
    'close': Rule(float64, 1 / 10000.0, 2),
    'high': Rule(float64, 1 / 10000.0, 2),
    'low': Rule(float64, 1 / 10000.0, 2),
    'limit_up': Rule(float64, 1 / 10000.0, 2),
    'limit_down': Rule(float64, 1 / 10000.0, 2),
    'basis_spread': Rule(float64, 1 / 10000.0, 4),
    'settlement': Rule(float64, 1 / 10000.0, 2),
    'prev_settlement': Rule(float64, 1 / 10000.0, 2),
})

FundDayBarConverter = Converter({
    'open': Rule(float64, 1 / 10000.0, 3),
    'close': Rule(float64, 1 / 10000.0, 3),
    'high': Rule(float64, 1 / 10000.0, 3),
    'low': Rule(float64, 1 / 10000.0, 3),
    'acc_net_value': Rule(float64, 1 / 10000.0, 4),
    'unit_net_value': Rule(float64, 1 / 10000.0, 4),
    'discount_rate': Rule(float64, 1 / 10000.0, 4),
    'limit_up': Rule(float64, 1/10000.0, 4),
    'limit_down': Rule(float64, 1/10000.0, 4),
})

IndexBarConverter = Converter({
    'open': Rule(float64, 1 / 10000.0, 2),
    'close': Rule(float64, 1 / 10000.0, 2),
    'high': Rule(float64, 1 / 10000.0, 2),
    'low': Rule(float64, 1 / 10000.0, 2),
})
