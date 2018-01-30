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

from rqalpha.model.base_account import BaseAccount
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, SIDE
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log

from ..api.api_future import order


def margin_of(order_book_id, quantity, price):
    env = Environment.get_instance()
    margin_info = env.data_proxy.get_margin_info(order_book_id)
    margin_multiplier = env.config.base.margin_multiplier
    margin_rate = margin_info['long_margin_ratio'] * margin_multiplier
    contract_multiplier = env.get_instrument(order_book_id).contract_multiplier
    return quantity * contract_multiplier * price * margin_rate


class FutureAccount(BaseAccount):

    __abandon_properties__ = [
        "daily_holding_pnl",
        "daily_realized_pnl"
    ]

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.SETTLEMENT, self._settlement)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_creation_reject)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        if self.AGGRESSIVE_UPDATE_LAST_PRICE:
            event_bus.add_listener(EVENT.BAR, self._on_bar)
            event_bus.add_listener(EVENT.TICK, self._on_tick)

    def fast_forward(self, orders, trades=list()):
        # 计算 Positions
        for trade in trades:
            if trade.exec_id in self._backward_trade_set:
                continue
            self._apply_trade(trade)
        # 计算 Frozen Cash
        self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def order(self, order_book_id, quantity, style, target=False):
        position = self.positions[order_book_id]
        if target:
            # For order_to
            quantity = quantity - position.buy_quantity + position.sell_quantity
        orders = []
        if quantity > 0:
            # 平昨仓
            if position.sell_old_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.sell_old_quantity),
                    SIDE.BUY,
                    POSITION_EFFECT.CLOSE,
                    style
                ))
                quantity -= position.sell_old_quantity
            if quantity <= 0:
                return orders
            # 平今仓
            if position.sell_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.sell_today_quantity),
                    SIDE.BUY,
                    POSITION_EFFECT.CLOSE_TODAY,
                    style
                ))
                quantity -= position.sell_today_quantity
            if quantity <= 0:
                return orders
            # 开多仓
            orders.append(order(
                order_book_id,
                quantity,
                SIDE.BUY,
                POSITION_EFFECT.OPEN,
                style
            ))
            return orders
        else:
            # 平昨仓
            quantity *= -1
            if position.buy_old_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.buy_old_quantity),
                    SIDE.SELL,
                    POSITION_EFFECT.CLOSE,
                    style
                ))
                quantity -= position.buy_old_quantity
            if quantity <= 0:
                return orders
            # 平今仓
            if position.buy_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.buy_today_quantity),
                    SIDE.SELL,
                    POSITION_EFFECT.CLOSE_TODAY,
                    style
                ))
                quantity -= position.buy_today_quantity
            if quantity <= 0:
                return orders
            # 开空仓
            orders.append(order(
                order_book_id,
                quantity,
                SIDE.SELL,
                POSITION_EFFECT.OPEN,
                style
            ))
            return orders

    def get_state(self):
        return {
            'positions': {
                order_book_id: position.get_state()
                for order_book_id, position in six.iteritems(self._positions)
            },
            'frozen_cash': self._frozen_cash,
            'total_cash': self._total_cash,
            'backward_trade_set': list(self._backward_trade_set),
            'transaction_cost': self._transaction_cost,
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])
        self._transaction_cost = state['transaction_cost']

        margin_changed = 0
        self._positions.clear()
        for order_book_id, v in six.iteritems(state['positions']):
            position = self._positions.get_or_create(order_book_id)
            position.set_state(v)
            if 'margin_rate' in v and abs(v['margin_rate'] - position.margin_rate) > 1e-6:
                margin_changed += position.margin * (v['margin_rate'] - position.margin_rate) / position.margin_rate

        self._total_cash = state['total_cash'] + margin_changed


    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE.name

    @staticmethod
    def _frozen_cash_of_order(order):
        if order.position_effect == POSITION_EFFECT.OPEN:
            return margin_of(order.order_book_id, order.unfilled_quantity, order.frozen_price)
        else:
            return 0

    @staticmethod
    def _frozen_cash_of_trade(trade):
        if trade.position_effect == POSITION_EFFECT.OPEN:
            return margin_of(trade.order_book_id, trade.last_quantity, trade.frozen_price)
        else:
            return 0

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
        total_value = self.total_value

        for position in list(self._positions.values()):
            order_book_id = position.order_book_id
            if position.is_de_listed() and position.buy_quantity + position.sell_quantity != 0:
                user_system_log.warn(
                    _(u"{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                del self._positions[order_book_id]
            elif position.buy_quantity == 0 and position.sell_quantity == 0:
                del self._positions[order_book_id]
            else:
                position.apply_settlement()
        self._total_cash = total_value - self.margin - self.holding_pnl

        # 如果 total_value <= 0 则认为已爆仓，清空仓位，资金归0
        if total_value <= 0:
            self._positions.clear()
            self._total_cash = 0

        self._backward_trade_set.clear()

    def _on_bar(self, event):
        for position in self._positions.values():
            position.update_last_price()

    def _on_tick(self, event):
        for position in self._positions.values():
            position.update_last_price()

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
        delta_cash = position.apply_trade(trade)

        self._transaction_cost += trade.transaction_cost
        self._total_cash -= trade.transaction_cost
        self._total_cash += delta_cash
        self._frozen_cash -= self._frozen_cash_of_trade(trade)
        self._backward_trade_set.add(trade.exec_id)

    # ------------------------------------ Abandon Property ------------------------------------

    @property
    def daily_holding_pnl(self):
        """
        [已弃用] 请使用 holding_pnl
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('future_account.daily_holding_pnl'))
        return self.holding_pnl

    @property
    def daily_realized_pnl(self):
        """
        [已弃用] 请使用 realized_pnl
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('future_account.daily_realized_pnl'))
        return self.realized_pnl
