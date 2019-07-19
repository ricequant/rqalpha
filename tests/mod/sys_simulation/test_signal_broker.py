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

from ...utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
    "base": {
        "start_date": "2015-04-10",
        "end_date": "2015-04-10",
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
        },
        "sys_simulation": {
            "signal": True,
        }
    },
}, test_strategies)


@as_test_strategy()
def test_price_limit():
    def handle_bar(context, bar_dict):
        stock = "000001.XSHE"
        order_shares(stock, 100, bar_dict[stock].limit_up)
        assert context.portfolio.positions[stock].quantity == 100
    return handle_bar
