#!/usr/bin/env python
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

from rqalpha.api import *

from ...utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "accounts": {
                "stock": 1000000,
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            }
        },
    }, test_strategies)


@as_test_strategy({
    "base": {
        "start_date": "2015-12-07",
        "end_date": "2016-01-05"
    }
})
def test_stock_account_settlement():
    import datetime

    def init(context):
        # 招商地产
        context.s = "000024.XSHE"
        context.fired = False
        context.total_value_before_delisted = None

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 20000)
            context.fired = True
        if context.now.date() == datetime.date(2015, 12, 29):
            context.total_value_before_delisted = context.portfolio.total_value
        if context.now.date() > datetime.date(2015, 12, 29):
            assert context.portfolio.total_value == context.total_value_before_delisted
    return init, handle_bar
