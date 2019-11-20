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

import six

from rqalpha.interface import AbstractAccount
from rqalpha.utils.repr import property_repr
from rqalpha.events import EVENT
from rqalpha.environment import Environment


class AssetAccount(AbstractAccount):

    __repr__ = property_repr

    def __init__(self, total_cash, positions, backward_trade_set=None, register_event=True):
        self._static_total_value = total_cash
        self._positions = positions
        self._frozen_cash = 0
        self._backward_trade_set = backward_trade_set if backward_trade_set is not None else set()
        if register_event:
            self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)

        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._on_before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)

        event_bus.add_listener(EVENT.BAR, self._update_last_price)
        event_bus.add_listener(EVENT.TICK, self._update_last_price)

    def get_state(self):
        """"""
        return {
            'positions': {
                order_book_id: position.get_state()
                for order_book_id, position in six.iteritems(self._positions)
            },
            'frozen_cash': self._frozen_cash,
            'static_total_value': self._static_total_value,
            'backward_trade_set': list(self._backward_trade_set),
        }

    def set_state(self, state):
        """"""
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])

        self._positions.clear()
        for order_book_id, v in six.iteritems(state['positions']):
            position = self._positions.get_or_create(order_book_id)
            position.set_state(v)

        if "static_total_value" in state:
            self._static_total_value = state["static_total_value"]
        else:
            static_total_value = state["total_cash"]
            for position in list(six.itervalues(self._positions)):
                try:
                    static_total_value += (position.margin - position.daily_pnl + position.transaction_cost)
                except RuntimeError:
                    # 新老结构切换之间发生退市的
                    static_total_value += position.margin
                    self._positions.pop(position.order_book_id)
            self._static_total_value = state["total_cash"] + self.margin - self.daily_pnl + self.transaction_cost

    def _update_last_price(self, _):
        for position in self._positions.values():
            position.update_last_price()

    def fast_forward(self, orders, trades=list()):
        """"""
        raise NotImplementedError

    def order(self, order_book_id, quantity, style, target=False):
        """"""
        raise NotImplementedError

    def _on_order_pending_new(self, event):
        raise NotImplementedError

    def _on_order_unsolicited_update(self, event):
        raise NotImplementedError

    def _on_trade(self, event):
        raise NotImplementedError

    def _on_settlement(self, event):
        raise NotImplementedError

    def _on_before_trading(self, event):
        raise NotImplementedError

    @property
    def type(self):
        """
        [enum] 账户类型
        """
        raise NotImplementedError

    @property
    def positions(self):
        """
        [dict] 持仓字典
        """
        return self._positions

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

        可用资金 = 总资金 - 冻结资金

        """
        return self.total_cash - self._frozen_cash

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(position.market_value for position in six.itervalues(self._positions))

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in six.itervalues(self._positions))

    @property
    def margin(self):
        """
        [float] 总保证金
        """
        return sum(position.margin for position in six.itervalues(self._positions))

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return sum(p.daily_pnl for p in six.itervalues(self._positions))

    @property
    def total_value(self):
        """
        [float] 账户总权益

        期货账户总权益 = 期货昨日总权益 + 当日盈亏

        """
        return self._static_total_value + self.daily_pnl

    @property
    def total_cash(self):
        """
        [float] 账户总资金

        期货账户总资金会受保证金变化的影响变化，期货账户总资金 = 总权益 - 保证金

        """
        return self._static_total_value + self.daily_pnl - self.margin

    @property
    def position_pnl(self):
        """
        [float] 昨仓盈亏
        """
        return sum(p.position_pnl for p in six.itervalues(self._positions))

    @property
    def trading_pnl(self):
        """
        [float] 交易盈亏
        """
        return sum(p.trading_pnl for p in six.itervalues(self._positions))
