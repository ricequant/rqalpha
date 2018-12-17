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
from rqalpha.environment import Environment

from ..utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2018-04-01",
            "end_date": "2018-05-01",
            "frequency": "1d",
            "accounts": {
                "future": 10000000000
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
        },
    }, test_strategies)


def assert_almost_equal(first, second):
    assert round(abs(first - second), 10) == 0


@as_test_strategy({
    "base": {
        "future_info": {
            "SC": {
                "close_commission_ratio": 0.0001,
                "open_commission_ratio": 0.0002,
                "commission_type": "BY_MONEY",
            }
        }
    }
})
def test_future_info():
    def init(context):
        context.f1 = "SC1809"
        subscribe_event(EVENT.TRADE, on_trade)

    def handle_bar(*_):
        buy_open("SC1809", 2)
        sell_close("SC1809", 2, close_today=False)

    def on_trade(_, event):
        trade = event.trade
        contract_multiplier = Environment.get_instance().data_proxy.instruments("SC1809").contract_multiplier
        if trade.position_effect == POSITION_EFFECT.OPEN:
            assert_almost_equal(
                trade.transaction_cost, 0.0002 * trade.last_quantity * trade.last_price * contract_multiplier
            )
        elif trade.position_effect == POSITION_EFFECT.CLOSE:
            assert_almost_equal(
                trade.transaction_cost, 0.0001 * trade.last_quantity * trade.last_price * contract_multiplier
            )
        else:
            assert trade.transaction_cost == 0

    return init, handle_bar
