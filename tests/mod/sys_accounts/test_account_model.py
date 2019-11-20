# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from datetime import date

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
        "start_date": "2018-12-25",
        "end_date": "2019-01-05"
    }
})
def test_stock_delist():
    import datetime

    def init(context):
        context.s = "000979.XSHE"
        context.fired = False
        context.total_value_before_delisted = None

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 20000)
            context.fired = True
        if context.now.date() == datetime.date(2018, 12, 27):
            context.total_value_before_delisted = context.portfolio.total_value
        if context.now.date() > datetime.date(2018, 12, 28):
            assert context.portfolio.total_value == context.total_value_before_delisted
    return init, handle_bar


@as_test_strategy({
    "base": {
        "start_date": "2012-06-04",
        "end_date": "2018-07-9"
    },
    "extra": {
        "log_level": "info"
    }
})
def test_stock_dividend():
    def init(context):
        context.s = "601088.XSHG"
        context.last_cash = None

    def handle_bar(context, _):
        if context.now.date() in (date(2012, 6, 8), date(2017, 7, 7), date(2018, 7, 6)):
            context.last_cash = context.portfolio.cash

        elif context.now.date() == date(2012, 6, 4):
            order_shares(context.s, 1000)
        elif context.now.date() == date(2012, 6, 18):
            assert context.portfolio.cash == context.last_cash + 900
        elif context.now.date() == date(2017, 7, 11):
            assert context.portfolio.cash == context.last_cash + 2970
        elif context.now.date() == date(2018, 7, 9):
            assert context.portfolio.cash == context.last_cash + 91

    return init, handle_bar


@as_test_strategy({
    "base": {
        "start_date": "2015-05-06",
        "end_date": "2015-05-20"
    }
})
def test_stock_transform():
    def init(context):
        context.s1 = "601299.XSHG"
        context.s2 = "601766.XSHG"

    def handle_bar(context, _):
        if context.now.date() == date(2015, 5, 6):
            order_shares(context.s1, 200)
        elif context.now.date() >= date(2015, 5, 20):
            assert int(context.portfolio.positions[context.s2].quantity) == 220

    return init, handle_bar
