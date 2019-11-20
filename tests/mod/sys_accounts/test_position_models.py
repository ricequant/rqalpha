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


@as_test_strategy()
def test_stock_sellable():
    def init(context):
        context.fired = False
        context.s = "000001.XSHE"

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 1000)
            sellable = context.portfolio.positions[context.s].sellable
            assert sellable == 0, "wrong sellable {}, supposed to be {}".format(sellable, 0)
            context.fired = True

    return init, handle_bar

