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


class Tick(object):
    def __init__(self, order_book_id, dt, snapshot):
        self._order_book_id = order_book_id
        self._dt = dt
        self._snapshot = snapshot

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def datetime(self):
        return self._dt

    @property
    def open(self):
        return self._snapshot['open']

    @property
    def last(self):
        return self._snapshot['last']

    @property
    def high(self):
        return self._snapshot['high']

    @property
    def low(self):
        return self._snapshot['low']

    @property
    def prev_close(self):
        return self._snapshot['prev_close']

    @property
    def volume(self):
        return self._snapshot['volume']

    @property
    def total_turnover(self):
        return self._snapshot['total_turnover']

    @property
    def open_interest(self):
        return self._snapshot['open_interest']

    @property
    def prev_settlement(self):
        return self._snapshot['prev_settlement']

    # FIXME use dynamic creation
    @property
    def b1(self):
        return self._snapshot['b1']

    @property
    def b2(self):
        return self._snapshot['b2']

    @property
    def b3(self):
        return self._snapshot['b3']

    @property
    def b4(self):
        return self._snapshot['b4']

    @property
    def b5(self):
        return self._snapshot['b5']

    @property
    def b1_v(self):
        return self._snapshot['b1_v']

    @property
    def b2_v(self):
        return self._snapshot['b2_v']

    @property
    def b3_v(self):
        return self._snapshot['b3_v']

    @property
    def b4_v(self):
        return self._snapshot['b4_v']

    @property
    def b5_v(self):
        return self._snapshot['b5_v']

    @property
    def a1(self):
        return self._snapshot['a1']

    @property
    def a2(self):
        return self._snapshot['a2']

    @property
    def a3(self):
        return self._snapshot['a3']

    @property
    def a4(self):
        return self._snapshot['a4']

    @property
    def a5(self):
        return self._snapshot['a5']

    @property
    def a1_v(self):
        return self._snapshot['a1_v']

    @property
    def a2_v(self):
        return self._snapshot['a2_v']

    @property
    def a3_v(self):
        return self._snapshot['a3_v']

    @property
    def a4_v(self):
        return self._snapshot['a4_v']

    @property
    def a5_v(self):
        return self._snapshot['a5_v']

    @property
    def limit_up(self):
        return self._snapshot['limit_up']

    @property
    def limit_down(self):
        return self._snapshot['limit_down']
