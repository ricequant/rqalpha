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

from enum import Enum


class Events(Enum):
    # 系统初始化后触发
    POST_SYSTEM_INIT = 'post_system_init'
    # 策略执行完init函数后触发
    POST_USER_INIT = 'post_user_init'
    # 策略证券池发生变化后触发
    POST_UNIVERSE_CHANGED = 'post_universe_changed'

    # 执行before_trading函数前触发
    PRE_BEFORE_TRADING = 'pre_before_trading'
    # 该事件会触发策略的before_trading函数
    BEFORE_TRADING = 'before_trading'
    # 执行before_trading函数后触发
    POST_BEFORE_TRADING = 'post_before_trading'

    # 执行handle_bar函数前触发
    PRE_BAR = 'pre_bar'
    # 该事件会触发策略的handle_bar函数
    BAR = 'bar'
    # 执行handle_bar函数后触发
    POST_BAR = 'post_bar'

    # 预定义事件，支持handle_tick后使用
    PRE_TICK = 'pre_tick'
    TICK = 'tick'
    POST_TICK = 'post_tick'

    # 在scheduler执行前触发
    PRE_SCHEDULED = 'pre_scheduled'
    # 在scheduler执行后触发
    POST_SCHEDULED = 'post_scheduled'

    # 执行after_trading函数前触发
    PRE_AFTER_TRADING = 'pre_after_trading'
    # 该事件会触发策略的after_trading函数
    AFTER_TRADING = 'after_trading'
    # 执行after_trading函数后触发
    POST_AFTER_TRADING = 'post_after_trading'

    # 结算前触发该事件
    PRE_SETTLEMENT = 'pre_settlement'
    # 触发结算事件
    SETTLEMENT = 'settlement'
    # 结算后触发该事件
    POST_SETTLEMENT = 'post_settlement'

    # 创建订单
    ORDER_PENDING_NEW = 'order_pending_new'
    # 创建订单成功
    ORDER_CREATION_PASS = 'order_creation_pass'
    # 创建订单失败
    ORDER_CREATION_REJECT = 'order_creation_reject'
    # 创建撤单
    ORDER_PENDING_CANCEL = 'order_pending_cancel'
    # 撤销订单成功
    ORDER_CANCELLATION_PASS = 'order_cancellation_pass'
    # 撤销订单失败
    ORDER_CANCELLATION_REJECT = 'order_cancellation_reject'
    # 订单状态更新
    ORDER_UNSOLICITED_UPDATE = 'order_unsolicited_update'

    # 成交
    TRADE = 'trade'

    ON_LINE_PROFILER_RESULT = 'on_line_profiler_result'
