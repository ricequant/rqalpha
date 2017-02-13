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

from .base_position import BasePosition, PositionClone
from .future_position import FuturePosition
from .stock_position import StockPosition


class Positions(dict):
    def __init__(self, position_type):
        super(Positions, self).__init__()
        self._position_type = position_type

    def __missing__(self, key):
        p = self._position_type(key)
        self[key] = p
        return p

    def _clone(self):
        ps = {}
        for order_book_id in self:
            ps[order_book_id] = self[order_book_id]._clone()
        return ps


class PositionsClone(dict):
    def __init__(self, position_type):
        super(PositionsClone, self).__init__()
        self._position_type = position_type

    def __missing__(self, key):
        p = PositionClone()
        position = self._position_type(key)
        for key in dir(position):
            if "__" in key:
                continue
            setattr(p, key, getattr(position, key))
        return p

    def __repr__(self):
        return str([order_book_id for order_book_id in self])

    def __iter__(self):
        for key in sorted(super(PositionsClone, self).keys()):
            yield key

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def keys(self):
        for key in sorted(super(PositionsClone, self).keys()):
            yield key
