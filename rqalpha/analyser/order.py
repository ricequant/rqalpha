# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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

import uuid

from ..const import ORDER_STATUS


def gen_order_id():
    return uuid.uuid4().hex


# TODO use nametuple to reduce memory

class Order(object):

    def __init__(self, dt, order_book_id, quantity, style):
        self.dt = dt
        self.order_book_id = order_book_id
        self._style = style
        self._order_id = gen_order_id()

        self.filled_shares = 0.0
        self.quantity = quantity
        self._reject_reason = ""

        self.status = ORDER_STATUS.OPEN

    @property
    def style(self):
        return self._style

    @property
    def order_id(self):
        return self._order_id

    @property
    def instrument(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError

    def fill(self, shares):
        self.filled_shares += shares

        assert self.filled_shares <= self.quantity

    def mark_rejected(self, reject_reason):
        self._reject_reason = reject_reason
        self.status = ORDER_STATUS.REJECTED

    @property
    def is_buy(self):
        return self.quantity > 0

    @property
    def reject_reason(self):
        return self._reject_reason

    def __repr__(self):
        return "Order({0})".format(self.__dict__)
