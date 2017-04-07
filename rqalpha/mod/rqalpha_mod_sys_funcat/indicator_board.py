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

from collections import defaultdict

from funcat import set_current_stock, set_current_dt


def wrapper_func(func):
    def wrap(*args, **kwargs):
        return func(*args, **kwargs)

    return wrap


class IndicatorBoard(object):
    def __init__(self, start_date, end_date):
        self._ind_func = {}
        self._result_board = defaultdict(dict)
        self._start_date = start_date
        self._end_date = end_date

    def set_current_dt(self, dt):
        set_current_dt(dt)

    def reg_indicator(self, name, func_obj):
        self._ind_func[name] = func_obj

    def get_indicator(self, order_book_id, name):
        set_current_stock(order_book_id)

        indicator_dict = self._result_board[order_book_id]
        if name not in indicator_dict:
            func_obj = self._ind_func[name]
            # 需要有一种方法分段计算、分段缓存
            self._result_board[name] = func_obj()

        # 如果缓存过期了，重新分段计算

        return self._result_board[name]
