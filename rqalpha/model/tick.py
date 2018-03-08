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
    def __init__(self, order_book_id, tick):
        self._order_book_id = order_book_id
        self._tick = tick

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def datetime(self):
        return self._tick['datetime']

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

    @property
    def asks(self):
        try:
            return self._tick['ask']
        except (KeyError, ValueError):
            # FIXME: forward compatbility
            return []

    @property
    def ask_vols(self):
        try:
            return self._tick['ask_vol']
        except (KeyError, ValueError):
            return []

    @property
    def bids(self):
        try:
            return self._tick["bid"]
        except (KeyError, ValueError):
            return []

    @property
    def bid_vols(self):
        try:
            return self._tick["bid_vol"]
        except (KeyError, ValueError):
            return []

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
