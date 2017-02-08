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

from enum import Enum


class Events(Enum):
    POST_SYSTEM_INIT = 'post_system_init'
    POST_USER_INIT = 'post_user_init'

    POST_UNIVERSE_CHANGED = 'post_universe_changed'

    PRE_BEFORE_TRADING = 'pre_before_trading'
    BEFORE_TRADING = 'before_trading'
    POST_BEFORE_TRADING = 'post_before_trading'

    PRE_BAR = 'pre_bar'
    BAR = 'bar'
    POST_BAR = 'post_bar'

    PRE_TICK = 'pre_tick'
    TICK = 'tick'
    POST_TICK = 'post_tick'

    PRE_SCHEDULED = 'pre_scheduled'
    POST_SCHEDULED = 'post_scheduled'

    PRE_AFTER_TRADING = 'pre_after_trading'
    AFTER_TRADING = 'after_trading'
    POST_AFTER_TRADING = 'post_after_trading'

    PRE_SETTLEMENT = 'pre_settlement'
    SETTLEMENT = 'settlement'
    POST_SETTLEMENT = 'post_settlement'

    ORDER_NEW = 'order_new'     # 新产生了一个 order
    ORDER_CREATION_PASS = 'order_creation_pass'
    ORDER_CREATION_REJECT = 'order_creation_reject'
    ORDER_CANCELLATION_PASS = 'order_cancellation_pass'
    ORDER_CANCELLATION_REJECT = 'order_cancellation_reject'
    ORDER__UNSOLICITED_UPDATE = 'order_unsolicited_update'

    TRADE = 'trade'

    ON_LINE_PROFILER_RESULT = 'on_line_profiler_result'
