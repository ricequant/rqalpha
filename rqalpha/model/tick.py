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

from rqalpha.utils.datetime_func import convert_date_time_ms_int_to_datetime


class Tick(object):
    def __init__(self, order_book_id, tick):
        self._order_book_id = order_book_id
        self._tick = tick

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def datetime(self):
        dt = convert_date_time_ms_int_to_datetime(self._tick["date"], self._tick["time"])
        return dt

    @property
    def open(self):
        return self._tick['open']

    @property
    def last(self):
        return self._tick['last']

    @property
    def high(self):
        return self._tick['high']

    @property
    def low(self):
        return self._tick['low']

    @property
    def prev_close(self):
        return self._tick['prev_close']

    @property
    def volume(self):
        return self._tick['volume']

    @property
    def total_turnover(self):
        return self._tick['total_turnover']

    @property
    def open_interest(self):
        return self._tick['open_interest']

    @property
    def prev_settlement(self):
        return self._tick['prev_settlement']

    # FIXME: use dynamic creation
    @property
    def b1(self):
        return self._tick['b1']

    @property
    def b2(self):
        return self._tick['b2']

    @property
    def b3(self):
        return self._tick['b3']

    @property
    def b4(self):
        return self._tick['b4']

    @property
    def b5(self):
        return self._tick['b5']

    @property
    def b1_v(self):
        return self._tick['b1_v']

    @property
    def b2_v(self):
        return self._tick['b2_v']

    @property
    def b3_v(self):
        return self._tick['b3_v']

    @property
    def b4_v(self):
        return self._tick['b4_v']

    @property
    def b5_v(self):
        return self._tick['b5_v']

    @property
    def a1(self):
        return self._tick['a1']

    @property
    def a2(self):
        return self._tick['a2']

    @property
    def a3(self):
        return self._tick['a3']

    @property
    def a4(self):
        return self._tick['a4']

    @property
    def a5(self):
        return self._tick['a5']

    @property
    def a1_v(self):
        return self._tick['a1_v']

    @property
    def a2_v(self):
        return self._tick['a2_v']

    @property
    def a3_v(self):
        return self._tick['a3_v']

    @property
    def a4_v(self):
        return self._tick['a4_v']

    @property
    def a5_v(self):
        return self._tick['a5_v']

    @property
    def limit_up(self):
        return self._tick['limit_up']

    @property
    def limit_down(self):
        return self._tick['limit_down']

    def __repr__(self):
        items = []
        for name in dir(self):
            if name.startswith("_"):
                continue
            items.append((name, getattr(self, name)))
        return "Tick({0})".format(', '.join('{0}: {1}'.format(k, v) for k, v in items))

    def __getitem__(self, key):
        return getattr(self, key)
