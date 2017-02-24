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

    @property
    def bid(self):
        return self._snapshot['bid']

    @property
    def bid_volume(self):
        return self._snapshot['bid_volume']

    @property
    def ask(self):
        return self._snapshot['ask']

    @property
    def ask_volume(self):
        return self._snapshot['ask_volume']

    @property
    def limit_up(self):
        return self._snapshot['limit_up']

    @property
    def limit_down(self):
        return self._snapshot['limit_down']
