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

from ...environment import Environment
from ...events import EVENT
from .base_account import BaseAccount
from ...const import ACCOUNT_TYPE, POSITION_EFFECT
from ...execution_context import ExecutionContext
from ...utils.i18n import gettext as _
from ...utils.logger import user_system_log


def margin_of(order_book_id, quantity, price):
    instrument = ExecutionContext.get_instrument(order_book_id)
    margin_rate = ExecutionContext.get_future_margin_rate(order_book_id)
    margin_multiplier = ExecutionContext.config.base.margin_multiplier
    return quantity * price * margin_multiplier * margin_rate * instrument.contract_multiplier


class FutureAccount(BaseAccount):

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_SETTLEMENT, self._settlement)
        event_bus.add_listener(EVENT.ORDER_PEDING_NEW, self._on_order_pending_new)
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
        self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order._is_active())

    @property
    def type(self):
        return ACCOUNT_TYPE.FUTURE

    @staticmethod
    def _frozen_cash_of_order(order):
        return margin_of(order.order_book_id, order.unfilled_quantity, order._frozen_price)

    @staticmethod
    def _frozen_cash_of_trade(trade):
        return margin_of(trade.order.order_book_id, trade.last_quantity, trade.order._frozen_price)

    @property
    def total_value(self):
        return self._total_cash + self.margin + self.daily_holding_pnl

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
        return self.daily_realized_pnl + self.daily_holding_pnl - self.transaction_cost

    @property
    def daily_holding_pnl(self):
        """
        [float] 浮动盈亏
        """
        return sum(position.daily_holding_pnl for position in six.itervalues(self._positions))

    @property
    def daily_realized_pnl(self):
        """
        [float] 平仓盈亏
        """
        return sum(position.daily_realized_pnl for position in six.iteritems(self._positions))

    def _settlement(self, event):
        for position in list(self._positions.values()):
            order_book_id = position.order_book_id
            if position.is_de_listed() and position.buy_quantity + position.sell_qauntity != 0:
                self._total_cash += position.market_value * position.contract_multiplier
                user_system_log.warn(
                    _("{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                self._positions.pop(order_book_id, None)
            elif position.buy_quantity == 0 and position.sell_qauntity == 0:
                self._positions.pop(order_book_id, None)
            else:
                position.apply_settlement()

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
        order_book_id = trade.order.order_book_id
        position = self._positions[order_book_id]

        self._total_cash -= trade.transaction_cost
        if trade.order.position_effect != POSITION_EFFECT.OPEN:
            self._total_cash -= trade.last_quantity * trade.last_price * position.margin_rate
        else:
            self._total_cash -= trade.last_quantity * trade.last_price * position.margin_rate
        self._frozen_cash -= self._frozen_cash_of_trade(trade)
        self._positions[order_book_id].apply_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
