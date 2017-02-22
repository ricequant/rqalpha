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

from rqalpha.const import SIDE, POSITION_EFFECT
from rqalpha.utils.i18n import gettext as _
from rqalpha.execution_context import ExecutionContext


class FrontendValidator(object):
    def __init__(self, config):
        self.config = config

    def order_pipeline(self, account, order):
        order_book_id = order.order_book_id
        bar_dict = ExecutionContext.get_current_bar_dict()
        portfolio = account.portfolio
        position = portfolio.positions[order_book_id]
        bar = bar_dict[order_book_id]

        if not self.validate_trading(order, bar):
            return False
        if not self.validate_available_cash(order, account, bar):
            return False
        if not self.validate_available_position(order, position):
            return False
        return True

    def validate_trading(self, order, bar):
        order_book_id = order.order_book_id
        trading_date = ExecutionContext.get_current_trading_dt().date()

        if bar.isnan:
            """
            只有未上市/已退市，对应的bar才为NaN
            """
            instrument = ExecutionContext.get_instrument(order_book_id)
            if trading_date < instrument.listed_date.date():
                order._mark_rejected(_("Order Rejected: {order_book_id} is not listed!").format(
                    order_book_id=order_book_id,
                ))
            elif trading_date > instrument.de_listed_date.date():
                order._mark_rejected(_("Order Rejected: {order_book_id} has been delisted!").format(
                    order_book_id=order_book_id,
                ))
            else:
                order._mark_rejected(_("Order Rejected: {order_book_id} is not trading!").format(
                    order_book_id=order_book_id,
                ))
            return False
        elif not bar.is_trading:
            """
            如果bar.is_trading为False，还需要判断是否为停盘，如果不是停牌，则说明交易量为0.
            """
            if bar.suspended:
                order._mark_rejected(_("Order Rejected: {order_book_id} is suspended!").format(
                    order_book_id=order_book_id,
                ))
                return False
        return True

    def validate_available_cash(self, order, account, bar):
        raise NotImplementedError

    def validate_available_position(self, order, position):
        raise NotImplementedError


class StockFrontendValidator(FrontendValidator):
    def validate_available_cash(self, order, account, bar):
        if not self.config.available_cash:
            return True
        if order.side != SIDE.BUY:
            return True
        # 检查可用资金是否充足
        cost_money = order._frozen_price * order.quantity
        if cost_money > account.portfolio.cash:
            order._mark_rejected(_(
                "Order Rejected: not enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=cost_money,
                cash=account.portfolio.cash,
            ))
            return False
        return True

    def validate_available_position(self, order, position):
        if not self.config.available_position:
            return True
        if order.side != SIDE.SELL:
            return True
        if order.quantity > position.sellable:
            order._mark_rejected(_(
                "Order Rejected: not enough stock {order_book_id} to sell, you want to sell {quantity}, sellable {sellable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                sellable=position.sellable,
            ))
            return False
        return True


class FutureFrontendValidator(FrontendValidator):
    def validate_available_cash(self, order, account, bar):
        if not self.config.available_cash:
            return True
        if order.position_effect != POSITION_EFFECT.OPEN:
            return True
        contract_multiplier = bar.instrument.contract_multiplier
        cost_money = account.margin_decider.cal_margin(order.order_book_id, order.side, order._frozen_price * order.quantity * contract_multiplier)
        if cost_money > account.portfolio.cash:
            order._mark_rejected(_(
                "Order Rejected: not enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=cost_money,
                cash=account.portfolio.cash,
            ))
            return False
        return True

    def validate_available_position(self, order, position):
        if not self.config.available_position:
            return True
        if order.position_effect != POSITION_EFFECT.CLOSE:
            return True
        if order.side == SIDE.BUY and order.quantity > position._sell_closable_quantity:
            order._mark_rejected(_(
                "Order Rejected: not enough securities {order_book_id} to buy close, target sell quantity is {quantity}, sell_closable_quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position._sell_closable_quantity,
            ))
            return False
        elif order.side == SIDE.SELL and order.quantity > position._buy_closable_quantity:
            order._mark_rejected(_(
                "Order Rejected: not enough securities {order_book_id} to sell close, target sell quantity is {quantity}, buy_closable_quantity {closable}").format(
                order_book_id=order.order_book_id,
                quantity=order.quantity,
                closable=position._buy_closable_quantity,
            ))
            return False
        return True
