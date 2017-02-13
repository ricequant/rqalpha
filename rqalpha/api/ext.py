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

from ..execution_context import ExecutionContext
from .api_base import instruments


def get_current_bar_dict():
    bar_dict = ExecutionContext.get_current_bar_dict()
    return bar_dict


def price_change(stock):
    bar_dict = get_current_bar_dict()
    return bar_dict[stock].close / bar_dict[stock].prev_close - 1


def symbol(order_book_id, split=", "):
    if isinstance(order_book_id, six.string_types):
        return "{}[{}]".format(order_book_id, instruments(order_book_id).symbol)
    else:
        s = split.join(symbol(item) for item in order_book_id)
        return s


def now_time_str(str_format="%H:%M:%S"):
    dt = ExecutionContext.get_current_trading_dt()
    return dt.strftime(str_format)
