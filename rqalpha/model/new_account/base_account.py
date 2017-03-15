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

from six import itervalues

from ...environment import Environment
from ...const import DAYS_CNT
from ...events import EVENT


class BaseAccount(object):
    def __init__(self, total_cash, daily_orders, daily_trades, positions, units, static_unit_net_value):
        config = Environment.get_instance().config
        self._start_date = config.base.start_date
        self._units = units
        self._static_unit_net_value = static_unit_net_value
        self._daily_orders = daily_orders
        self._daily_trades = daily_trades
        self._positions = positions
        self._frozen_cash = self._cal_frozen_cash([order for order in daily_orders if order._is_active()])
        self._cash = total_cash - self._frozen_cash
        self._type = self._get_type()
        self._current_date = None
        self._register_event()

    def _get_starting_cash(self):
        raise NotImplementedError

    def _get_type(self):
        raise NotImplementedError

    @staticmethod
    def _cal_frozen_cash(daily_orders):
        raise NotImplementedError

    def _register_event(self):
        event_bus = Environment.get_instance().event_bus

        # 该事件会触发策略的before_trading函数
        event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # 该事件会触发策略的handle_bar函数
        event_bus.add_listener(EVENT.BAR, self.bar)
        # 该事件会触发策略的handel_tick函数
        event_bus.add_listener(EVENT.TICK, self.tick)
        # 该事件会触发策略的after_trading函数
        event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)
        # 触发结算事件
        event_bus.add_listener(EVENT.SETTLEMENT, self.settlement)

        # 创建订单
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self.order_pending_new)
        # 创建订单成功
        event_bus.add_listener(EVENT.ORDER_CREATION_PASS, self.order_creation_pass)
        # 创建订单失败
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self.order_creation_reject)
        # 创建撤单
        event_bus.add_listener(EVENT.ORDER_PENDING_CANCEL, self.order_pending_cancel)
        # 撤销订单成功
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self.order_cancellation_pass)
        # 撤销订单失败
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_REJECT, self.order_cancellation_reject)
        # 订单状态更新
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self.order_unsolicited_update)
        # 成交
        event_bus.add_listener(EVENT.TRADE, self.trade)

    @property
    def type(self):
        return self._type

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        raise NotImplementedError

    @property
    def total_value(self):
        """
        总权益
        """
        raise NotImplementedError

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        raise NotImplementedError

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        return self._positions

    @property
    def units(self):
        """
        [float] 份额
        """
        return self._units

    @property
    def start_date(self):
        """
        [datetime.datetime] 策略投资组合的开始日期
        :return:
        """
        return self._start_date

    @property
    def frozen_cash(self):
        """
        [float] 冻结资金
        """
        return self._frozen_cash

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return self._cash

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(position.market_value for position in itervalues(self._positions))

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in itervalues(self._positions))

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        Note: 如果存在出入金的情况，需要同时更新starting_cash
        """
        return self.unit_net_value * self._units - self._get_starting_cash()

    @property
    def daily_returns(self):
        """
        [float] 当前最新一天的日收益
        """
        return 0 if self._static_unit_net_value == 0 else self.unit_net_value / self._static_unit_net_value - 1

    @property
    def total_returns(self):
        """
        [float] 累计收益率
        """
        return self.unit_net_value - 1

    @property
    def annualized_returns(self):
        """
        [float] 累计年化收益率
        """
        return self.unit_net_value ** (
        DAYS_CNT.DAYS_A_YEAR / float((self._current_date - self.start_date).days + 1)) - 1

    @property
    def portfolio_value(self):
        """
        [Deprecated] 总权益
        """
        return self.total_value

    def before_trading(self, event):
        """
        该事件会触发策略的before_trading函数
        """
        pass

    def bar(self, event):
        """
        该事件会触发策略的handle_bar函数
        """
        pass

    def tick(self, event):
        """
        该事件会触发策略的handel_tick函数
        """
        pass

    def after_trading(self, event):
        """
        该事件会触发策略的after_trading函数
        """
        pass

    def settlement(self, event):
        """
        触发结算事件
        """
        pass

    def order_pending_new(self, event):
        """
        创建订单
        """
        pass

    def order_creation_pass(self, event):
        """
        创建订单成功
        """
        pass

    def order_creation_reject(self, event):
        """
        创建订单失败
        """
        pass

    def order_pending_cancel(self, event):
        """
        创建撤单
        """
        pass

    def order_cancellation_pass(self, event):
        """
        撤销订单成功
        """
        pass

    def order_cancellation_reject(self, event):
        """
        撤销订单失败
        """
        pass

    def order_unsolicited_update(self, event):
        """
        订单状态更新
        """
        pass

    def trade(self, event):
        """
        成交
        """
        pass
