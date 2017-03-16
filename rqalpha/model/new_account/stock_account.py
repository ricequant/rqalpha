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

from ...events import EVENT
from ...environment import Environment
from ...model.position import Positions
from ..new_position.stock_position import StockPosition
from ...utils.logger import user_system_log
from ...utils.i18n import gettext as _
from ...const import SIDE
from ...execution_context import ExecutionContext


class StockAccount(object):
    def __init__(self, start_date, starting_cash,
                 static_unit_net_value, units, cash, frozen_cash=0,
                 positions=Positions(StockPosition), dividend_receivable=None):
        self._start_date = start_date
        self._starting_cash = starting_cash
        self._cash = cash
        self._units = units
        self._static_unit_net_value = static_unit_net_value

        self._positions = positions
        self._frozen_cash = frozen_cash
        self._dividend_receivable = dividend_receivable if dividend_receivable else {}

        # cached value
        self._market_value = None

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_creation_reject)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._before_trading)
        event_bus.add_listener(EVENT.PRE_AFTER_TRADING, self._after_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)

    def _on_trade(self, event):
        self._market_value = None
        trade = event.trade
        position = self._positions[trade.order_book_id]
        self._cash -= trade.transaction_cost
        if trade.side == SIDE.BUY:
            self._cash -= trade.last_quantity * trade.last_price
            self._frozen_cash -= trade.order._frozen_price * trade.last_quantity
            position.apply_trade_(trade)
        else:
            self._cash += trade.last_price * trade.last_quantity

    def _on_order_pending_new(self, event):
        order = event.order
        position = self._positions[order.order_book_id]
        position.on_order_pending_new_(order)
        if order.side == SIDE.BUY:
            order_value = order._frozen_price * order.quantity
            self._frozen_cash += order_value

    def _on_order_creation_reject(self, event):
        order = event.order
        position = self._positions[order.order_book_id]
        position.on_order_creation_reject_(order)
        if order.side == SIDE.BUY:
            order_value = order._frozen_price * order.quantity
            self._frozen_cash -= order_value

    def _on_order_unsolicited_update(self, event):
        order = event.order
        position = self._positions[order.order_book_id]
        position.on_order_cancel_(order)
        if order.side == SIDE.BUY:
            unfilled_value = order.unfilled_quantity * order._frozen_price
            self._frozen_cash -= unfilled_value

    def _before_trading(self, event):
        self._market_value = None
        removed = [order_book_id for order_book_id, position in six.iteritems(self._positions)
                   if position.quantity == 0]
        for order_book_id in removed:
            del self._positions[order_book_id]
        self._handle_dividend_payable(event.trading_dt.date())
        if ExecutionContext.config.base.handle_split:
            self._handle_split(event.trading_dt.date())

    def _after_trading(self, event):
        self._market_value = None
        data_proxy = ExecutionContext.get_data_proxy()
        de_listed = []
        for order_book_id in six.iterkeys(self._positions):
            instrument = data_proxy.instruments(order_book_id)
            if instrument.de_listed_date <= event.trading_dt:
                de_listed.append(order_book_id)
        for order_book_id in de_listed:
            position = self._positions[order_book_id]
            if ExecutionContext.config.validator.cash_return_by_stock_delisted:
                self._cash += position.market_value
            if position.quantity != 0:
                user_system_log.warn(
                    _("{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id)
                )
            del self._positions[order_book_id]
        for position in six.itervalues(self._positions):
            position.after_trading_()

    def _on_settlement(self, event):
        self._static_unit_net_value = self.unit_net_value

    @property
    def unit_net_value(self):
        return self.portfolio_value / self._units

    def _handle_dividend_payable(self, trading_date):
        to_be_removed = []
        for order_book_id, dividend in six.iteritems(self._dividend_receivable):
            if dividend['payable_date'] == trading_date:
                to_be_removed.append(order_book_id)
                self._cash += dividend['quantity'] * dividend['dividend_per_share']
        for order_book_id in to_be_removed:
            del self._dividend_receivable[order_book_id]

    def _handle_dividend_book_closure(self, trading_date):
        data_proxy = ExecutionContext.get_data_proxy()
        for order_book_id, position in six.iteritems(self._positions):
            dividend = data_proxy.get_dividend_by_book_date(order_book_id, trading_date)
            if dividend is None:
                continue

            dividend_per_share = dividend['dividend_cash_before_tax'] / dividend['round_lot']
            self._dividend_receivable[order_book_id] = {
                'quantity': position.quantity,
                'dividend_per_share': dividend_per_share,
                'payable_date': dividend['payable_date'].date()
            }

    def _handle_split(self, trading_date):
        data_proxy = ExecutionContext.get_data_proxy()
        for order_book_id, position in six.iteritems(self._positions):
            split = data_proxy.get_split_by_ex_date(order_book_id, trading_date)
            if split is None:
                continue
            ratio = split['split_coefficient_to'] / split['split_coefficient_from']
            position.split_(ratio)

    @property
    def cash(self):
        """
        【float】可用资金
        """
        return self._cash - self._frozen_cash

    @property
    def positions(self):
        """
        【dict】一个包含股票子组合仓位的字典，以order_book_id作为键，position对象作为值，
        关于position的更多的信息可以在下面的部分找到。
        """
        return self._positions

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，当日投资组合总权益-昨日投资组合总权益
        """
        return self.market_value - self._units * self._static_unit_net_value

    @property
    def pnl(self):
        return self.market_value - self._starting_cash

    @property
    def market_value(self):
        """
        【float】总权益，包含市场价值和剩余现金
        """
        if self._market_value is None:
            # 总资金 + Sum(position._position_value)
            self._market_value = self._cash + sum(
                position.market_value for position in six.itervalues(self._positions))

        return self._market_value

    @property
    def total_value(self):
        return self.market_value

    @property
    def units(self):
        return self._units

    @property
    def start_date(self):
        return self._start_date

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in six.itervalues(self._positions))

    @property
    def daily_returns(self):
        return self.unit_net_value / self._static_unit_net_value if self._static_unit_net_value != 0 else 0

    @property
    def total_returns(self):
        return self.unit_net_value - 1

    @property
    def portfolio_value(self):
        """deprecated"""
        return self.market_value

    @property
    def dividend_receivable(self):
        """
        【float】投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分
        """
        return sum(d['quantity'] * d['dividend_per_share'] for d in six.iteritems(self._dividend_receivable))
