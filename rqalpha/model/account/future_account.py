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

import six

from .base_account import BaseAccount
from ...environment import Environment
from ...events import EVENT
from ...const import ACCOUNT_TYPE, POSITION_EFFECT
from ...utils.i18n import gettext as _
from ...utils.logger import user_system_log


def margin_of(order_book_id, quantity, price):
    env = Environment.get_instance()
    contract_multiplier = env.get_instrument(order_book_id).contract_multiplier
    margin_rate = env.get_future_margin_rate(order_book_id)
    margin_multiplier = env.config.base.margin_multiplier
    return quantity * price * margin_multiplier * margin_rate * contract_multiplier


class FutureAccount(BaseAccount):
    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.SETTLEMENT, self._settlement)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_creation_reject)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.TRADE, self._on_trade)

    def fast_forward(self, orders, trades=list()):
        # 计算 Positions
        for trade in trades:
            if trade.exec_id in self._backward_trade_set:
                continue
            self._apply_trade(trade)
        # 计算 Frozen Cash
        self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def get_state(self):
        return {
            'positions': {
                order_book_id: position.get_state()
                for order_book_id, position in six.iteritems(self._positions)
                },
            'frozen_cash': self._frozen_cash,
            'total_cash': self._total_cash,
            'backward_trade_set': list(self._backward_trade_set),
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._total_cash = state['total_cash']
        self._backward_trade_set = set(state['backward_trade_set'])
        self._positions.clear()
        for order_book_id, v in six.iteritems(state['positions']):
            position = self._positions.get_or_create(order_book_id)
            position.set_state(v)

    @property
    def type(self):
        return ACCOUNT_TYPE.FUTURE

    @staticmethod
    def _frozen_cash_of_order(order):
        return margin_of(order.order_book_id, order.unfilled_quantity, order.frozen_price)

    @staticmethod
    def _frozen_cash_of_trade(trade):
        return margin_of(trade.order_book_id, trade.last_quantity, trade.frozen_price)

    @property
    def total_value(self):
        return self._total_cash + self.margin + self.holding_pnl

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 总保证金
        """
        return sum(position.margin for position in six.itervalues(self._positions))

    @property
    def buy_margin(self):
        """
        [float] 买方向保证金
        """
        return sum(position.buy_margin for position in six.itervalues(self._positions))

    @property
    def sell_margin(self):
        """
        [float] 卖方向保证金
        """
        return sum(position.sell_margin for position in six.itervalues(self._positions))

    # -- PNL 相关
    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.realized_pnl + self.holding_pnl - self.transaction_cost

    @property
    def holding_pnl(self):
        """
        [float] 浮动盈亏
        """
        return sum(position.holding_pnl for position in six.itervalues(self._positions))

    @property
    def realized_pnl(self):
        """
        [float] 平仓盈亏
        """
        return sum(position.realized_pnl for position in six.itervalues(self._positions))

    def _settlement(self, event):
        old_margin = self.margin
        old_daily_pnl = self.daily_pnl + self.transaction_cost
        for position in list(self._positions.values()):
            order_book_id = position.order_book_id
            if position.is_de_listed() and position.buy_quantity + position.sell_quantity != 0:
                self._total_cash += position.market_value * position.margin_rate
                user_system_log.warn(
                    _(u"{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                del self._positions[order_book_id]
            elif position.buy_quantity == 0 and position.sell_quantity == 0:
                del self._positions[order_book_id]
            else:
                position.apply_settlement()
        self._total_cash = self._total_cash + (old_margin - self.margin) + old_daily_pnl

        self._backward_trade_set.clear()

    def _on_order_pending_new(self, event):
        if self != event.account:
            return
        self._frozen_cash += self._frozen_cash_of_order(event.order)

    def _on_order_creation_reject(self, event):
        if self != event.account:
            return
        self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_order_unsolicited_update(self, event):
        if self != event.account:
            return
        self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_trade(self, event):
        if self != event.account:
            return
        self._apply_trade(event.trade)

    def _apply_trade(self, trade):
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        position = self._positions.get_or_create(order_book_id)
        position.apply_trade(trade)

        self._total_cash -= trade.transaction_cost
        if trade.position_effect != POSITION_EFFECT.OPEN:
            self._total_cash += margin_of(order_book_id, trade.last_quantity, trade.last_price)
        else:
            self._total_cash -= margin_of(order_book_id, trade.last_quantity, trade.last_price)
        self._frozen_cash -= self._frozen_cash_of_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
