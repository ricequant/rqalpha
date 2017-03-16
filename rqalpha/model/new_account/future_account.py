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
from ...const import ACCOUNT_TYPE
from ...execution_context import ExecutionContext
from ...utils.i18n import gettext as _
from ...utils.logger import user_system_log


def margin_of(order_book_id, quantity, price):
    instrument = ExecutionContext.get_instrument(order_book_id)
    margin_rate = ExecutionContext.get_future_margin_rate(order_book_id)
    margin_multiplier = ExecutionContext.config.base.margin_multiplier
    return quantity * price * margin_multiplier * margin_rate * instrument.contract_multiplier


class FutureAccount(BaseAccount):
    def __init__(self, start_date, starting_cash, static_unit_net_value, units,
                 cash, frozen_cash, positions):
        super(self, FutureAccount).__init__(start_date, starting_cash, static_unit_net_value,
                                            units, cash, frozen_cash, positions)

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_SETTLEMENT, self._settlement)
        event_bus.add_listener(EVENT.ORDER_PEDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_creation_reject)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        event_bus.add_listener(EVENT.PRE_BAR, self._on_bar)
        event_bus.add_listener(EVENT.PRE_TICK, self._on_tick)

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
    def cash(self):
        """
        [float] 可用资金
        """
        return self.total_value - self.margin - self.daily_holding_pnl - self.frozen_cash

    @property
    def total_value(self):
        return self._static_unit_net_value * self.units + self.daily_pnl

    @property
    def unit_net_value(self):
        return self.total_value / self.units

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 总保证金
        """
        return sum(position.margin for position in six.itervalues(self.positions))

    @property
    def buy_margin(self):
        """
        [float] 买方向保证金
        """
        return sum(position.buy_margin for position in six.itervalues(self.positions))

    @property
    def sell_margin(self):
        """
        [float] 卖方向保证金
        """
        return sum(position.sell_margin for position in six.itervalues(self.positions))

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
        return sum(position.daily_holding_pnl for position in six.itervalues(self.positions))

    @property
    def daily_realized_pnl(self):
        """
        [float] 平仓盈亏
        """
        return sum(position.daily_realized_pnl for position in six.iteritems(self.positions))

    def _on_bar(self, event):
        bar_dict = event.bar_dict
        for order_book_id, position in six.iteritems(self._positions):
            bar = bar_dict[order_book_id]
            if bar.isnan:
                continue
            position.last_price = bar.close

    def _on_tick(self, event):
        tick = event.tick
        if tick.order_book_id in self._positions:
            self._positions[tick.order_book_id].last_price = tick.last

    def _settlement(self, event):
        for position in list(self.positions.values()):
            if position.is_de_listed():
                order_book_id = position.order_book_id
                user_system_log.warn(
                    _("{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                self.positions.pop(order_book_id, None)
            elif position._quantity == 0:
                # XXX seems wrong here @Eric
                self.positions.pop(position.order_book_id, None)
            else:
                position.apply_settlement()

        self._static_unit_net_value = self.unit_net_value

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
        trade = event.trade
        order_book_id = trade.order.order_book_id
        self._frozen_cash -= self._frozen_cash_of_trade(trade)
        self._positions[order_book_id].apply_trade(trade)
