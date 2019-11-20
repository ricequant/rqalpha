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

from rqalpha.environment import Environment
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, SIDE
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.utils.i18n import gettext as _

from ..api.api_future import order
from .asset_account import AssetAccount


def margin_of(order_book_id, quantity, price):
    env = Environment.get_instance()
    margin_multiplier = env.config.base.margin_multiplier
    instrument = env.get_instrument(order_book_id)
    return quantity * instrument.contract_multiplier * price * instrument.margin_rate * margin_multiplier


class FutureAccount(AssetAccount):

    forced_liquidation = True

    __abandon_properties__ = [
        "holding_pnl",
        "realized_pnl",
    ]

    def fast_forward(self, orders, trades=None):
        # 计算 Positions
        if trades:
            close_trades = []
            # 先处理开仓
            for trade in trades:
                if trade.exec_id in self._backward_trade_set:
                    continue
                if trade.position_effect == POSITION_EFFECT.OPEN:
                    self._apply_trade(trade)
                else:
                    close_trades.append(trade)
            # 后处理平仓
            for trade in close_trades:
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
            sell_old_quantity, sell_today_quantity = position.sell_old_quantity, position.sell_today_quantity
            # 平昨仓
            if sell_old_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, sell_old_quantity),
                    SIDE.BUY,
                    POSITION_EFFECT.CLOSE,
                    style
                ))
                quantity -= sell_old_quantity
            if quantity <= 0:
                return orders
            # 平今仓
            if sell_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, sell_today_quantity),
                    SIDE.BUY,
                    POSITION_EFFECT.CLOSE_TODAY,
                    style
                ))
                quantity -= sell_today_quantity
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
            buy_old_quantity, buy_today_quantity = position.buy_old_quantity, position.buy_today_quantity
            if buy_old_quantity > 0:
                orders.append(
                    order(order_book_id, min(quantity, buy_old_quantity), SIDE.SELL, POSITION_EFFECT.CLOSE, style))
                quantity -= min(quantity, buy_old_quantity)
            if quantity <= 0:
                return orders
            # 平今仓
            if buy_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, buy_today_quantity),
                    SIDE.SELL,
                    POSITION_EFFECT.CLOSE_TODAY,
                    style
                ))
                quantity -= buy_today_quantity
            if quantity <= 0:
                return orders
            # 开空仓
            orders.append(order(order_book_id, quantity, SIDE.SELL, POSITION_EFFECT.OPEN, style))
            return orders

    def _on_order_pending_new(self, event):
        if self != event.account:
            return

        self._frozen_cash += self._frozen_cash_of_order(event.order)

    def _on_order_unsolicited_update(self, event):
        if self != event.account:
            return
        order = event.order
        if order.filled_quantity != 0:
            self._frozen_cash -= order.unfilled_quantity / order.quantity * self._frozen_cash_of_order(order)
        else:
            self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_trade(self, event):
        if self != event.account:
            return
        self._apply_trade(event.trade, event.order)

    def _on_settlement(self, event):
        self._static_total_value = self.total_value

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

        # 如果 total_value <= 0 则认为已爆仓，清空仓位，资金归0
        if self._static_total_value <= 0 and self.forced_liquidation:
            if self._positions:
                user_system_log.warn(_("Trigger Forced Liquidation, current total_value is 0"))
            self._positions.clear()
            self._static_total_value = 0

        self._backward_trade_set.clear()

    def _on_before_trading(self, event):
        pass

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE.name

    @staticmethod
    def _frozen_cash_of_order(order):
        order_cost = margin_of(
            order.order_book_id, order.quantity, order.frozen_price
        ) if order.position_effect == POSITION_EFFECT.OPEN else 0
        return order_cost + Environment.get_instance().get_order_transaction_cost(
            DEFAULT_ACCOUNT_TYPE.FUTURE, order
        )

    def _apply_trade(self, trade, order=None):
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        self._positions.get_or_create(order_book_id).apply_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
        if order:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * self._frozen_cash_of_order(order)
            else:
                self._frozen_cash -= self._frozen_cash_of_order(order)

    @property
    def buy_margin(self):
        """
        [float] 多方向保证金
        """
        return sum(position.buy_margin for position in six.itervalues(self._positions))

    @property
    def sell_margin(self):
        """
        [float] 空方向保证金
        """
        return sum(position.sell_margin for position in six.itervalues(self._positions))

    # deprecated propertie
    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
