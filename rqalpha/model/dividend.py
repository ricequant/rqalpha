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

import six

DividendPersistMap = {
    "order_book_id": "order_book_id",
    "quantity": "quantity",
    "dividend_series_dict": "dividend_series_dict",
}


class Dividend(object):
    def __init__(self, order_book_id, quantity, dividend_series_dict):
        self.order_book_id = order_book_id
        self.quantity = quantity
        self.dividend_series_dict = dividend_series_dict

    @classmethod
    def __from_dict__(cls, dividend_dict):
        return cls(dividend_dict['order_book_id'], dividend_dict["quantity"], dividend_dict["dividend_series_dict"])

    def __to_dict__(self):
        dividend_dict = {}
        for persist_key, origin_key in six.iteritems(DividendPersistMap):
            dividend_dict[persist_key] = getattr(self, origin_key)
        return dividend_dict
