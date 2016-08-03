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


import pandas as pd

from . import ExecutionContext, get_last_date
from ..const import EXECUTION_PHASE


class HybridDataFrame(pd.DataFrame):

    def __init__(self, *args, **kwargs):
        missing_handler = kwargs.pop("missing_handler")
        super(HybridDataFrame, self).__init__(*args, **kwargs)
        self.missing_handler = missing_handler
        self._cache = {}

    def __getitem__(self, key):
        try:
            # return self._cache[key]
            return super(HybridDataFrame, self).__getitem__(key)
        except KeyError as e:
            if not isinstance(key, str) or self.missing_handler is None:
                raise
            try:
                rv = self.missing_handler(key)
            except KeyError:
                raise e
            self[key] = rv
            # self._cache[key] = rv
            return rv


def missing_handler(key, bar_count, frequency, field):
    order_book_id = key
    data_proxy = ExecutionContext.get_strategy_executor().data_proxy

    if frequency == '1m':
        raise RuntimeError('Minute bar not supported yet!')

    dt = ExecutionContext.get_current_dt().date()
    if ExecutionContext.get_active().phase == EXECUTION_PHASE.BEFORE_TRADING:
        dt = get_last_date(ExecutionContext.get_trading_params().trading_calendar, dt)

    hist = data_proxy.history(order_book_id, dt, bar_count, frequency, field)
    series = hist

    executor = ExecutionContext.get_strategy_executor()
    executor.current_universe.add(key)

    return series
