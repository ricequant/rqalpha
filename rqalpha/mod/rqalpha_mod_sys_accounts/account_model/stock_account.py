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
import datetime
from collections import defaultdict

import numpy as np

from rqalpha.environment import Environment
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.const import SIDE, DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT
from rqalpha.model.trade import Trade

from ..api.api_stock import order_shares
from .asset_account import AssetAccount


class StockAccount(AssetAccount):
    dividend_reinvestment = False

    __abandon_properties__ = []

    def __init__(self, total_cash, positions, backward_trade_set=None, dividend_receivable=None, register_event=True):
        super(StockAccount, self).__init__(total_cash, positions, backward_trade_set, register_event)
        self._dividend_receivable = dividend_receivable if dividend_receivable else {}
        self._pending_transform = {}

    def fast_forward(self, orders, trades=None):
        # 计算 Positions
        if trades:
            for trade in trades:
                if trade.exec_id in self._backward_trade_set:
                    continue
                self._apply_trade(trade)
        # 计算 Frozen Cash
        self._frozen_cash = 0
        frozen_quantity = defaultdict(int)
        for o in orders:
            if o.is_final():
                continue
            if o.side == SIDE.BUY:
                self._frozen_cash += self._frozen_cash_of_order(o)
            else:
                frozen_quantity[o.order_book_id] += o.unfilled_quantity
        for order_book_id, position in six.iteritems(self._positions):
            position.reset_frozen(frozen_quantity[order_book_id])

    def order(self, order_book_id, quantity, style, target=False):
        position = self.positions[order_book_id]
        if target:
            # For order_to
            quantity = quantity - position.quantity
        return order_shares(order_book_id, quantity, style=style)

    def _on_order_pending_new(self, event):
        if event.account != self:
            return
        order = event.order
        self._frozen_cash += self._frozen_cash_of_order(order)

    def _on_order_unsolicited_update(self, event):
        if event.account != self:
            return
        order = event.order
        if order.filled_quantity != 0:
            self._frozen_cash -= order.unfilled_quantity / order.quantity * self._frozen_cash_of_order(order)
        else:
            self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_trade(self, event):
        if event.account != self:
            return
        self._apply_trade(event.trade, event.order)

    def _on_before_trading(self, event):
        trading_date = Environment.get_instance().trading_dt.date()
        last_date = Environment.get_instance().data_proxy.get_previous_trading_date(trading_date)
        self._handle_dividend_book_closure(last_date)
        self._handle_dividend_payable(trading_date)
        self._handle_split(trading_date)
        self._handle_transform()

    def _on_settlement(self, event):
        env = Environment.get_instance()
        self._static_total_value = super(StockAccount, self).total_value
        for position in list(self._positions.values()):
            order_book_id = position.order_book_id
            if position.is_de_listed() and position.quantity != 0:
                try:
                    transform_data = env.data_proxy.get_share_transformation(order_book_id)
                except NotImplementedError:
                    pass
                else:
                    if transform_data is not None:
                        self._pending_transform[order_book_id] = transform_data
                        continue
                if not env.config.mod.sys_accounts.cash_return_by_stock_delisted:
                    self._static_total_value -= position.market_value
                user_system_log.warn(
                    _(u"{order_book_id} is expired, close all positions by system").format(
                        order_book_id=order_book_id)
                )
                self._positions.pop(order_book_id, None)
            elif position.quantity == 0:
                self._positions.pop(order_book_id, None)
            else:
                position.apply_settlement()

        self._backward_trade_set.clear()

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK.name

    def get_state(self):
        state = super(StockAccount, self).get_state()
        state.update({
            'dividend_receivable': self._dividend_receivable,
            'pending_transform': self._pending_transform,
        })
        return state

    def set_state(self, state):
        super(StockAccount, self).set_state(state)
        self._dividend_receivable = state['dividend_receivable']
        self._pending_transform = state.get("pending_transform", {})

    def _apply_trade(self, trade, order=None):
        if trade.exec_id in self._backward_trade_set:
            return

        position = self._positions.get_or_create(trade.order_book_id)
        position.apply_trade(trade)
        if order:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * self._frozen_cash_of_order(order)
            else:
                self._frozen_cash -= self._frozen_cash_of_order(order)
        self._backward_trade_set.add(trade.exec_id)

    def _handle_dividend_payable(self, trading_date):
        to_be_removed = []
        for order_book_id, dividend in six.iteritems(self._dividend_receivable):
            if dividend['payable_date'] == trading_date:
                to_be_removed.append(order_book_id)
                self._static_total_value += dividend['quantity'] * dividend['dividend_per_share']
        for order_book_id in to_be_removed:
            del self._dividend_receivable[order_book_id]

    @staticmethod
    def _int_to_date(d):
        r, d = divmod(d, 100)
        y, m = divmod(r, 100)
        return datetime.date(year=y, month=m, day=d)

    @staticmethod
    def _frozen_cash_of_order(order):
        order_cost = order.frozen_price * order.quantity if order.side == SIDE.BUY else 0
        return order_cost + Environment.get_instance().get_order_transaction_cost(DEFAULT_ACCOUNT_TYPE.STOCK, order)

    def _handle_dividend_book_closure(self, trading_date):
        for order_book_id, position in six.iteritems(self._positions):
            if position.quantity == 0:
                continue

            dividend = Environment.get_instance().data_proxy.get_dividend_by_book_date(order_book_id, trading_date)
            if dividend is None:
                continue

            dividend_per_share = sum(dividend['dividend_cash_before_tax'] / dividend['round_lot'])
            if np.isnan(dividend_per_share):
                raise RuntimeError("Dividend per share of {} is not supposed to be nan.".format(order_book_id))

            position.dividend_(dividend_per_share)

            if StockAccount.dividend_reinvestment:
                last_price = position.last_price
                dividend_value = position.quantity * dividend_per_share
                self._static_total_value += dividend_value
                self._apply_trade(Trade.__from_create__(
                    None, last_price, dividend_value / last_price, SIDE.BUY, POSITION_EFFECT.OPEN, order_book_id
                ))
            else:
                self._dividend_receivable[order_book_id] = {
                    'quantity': position.quantity,
                    'dividend_per_share': dividend_per_share,
                }

                try:
                    self._dividend_receivable[order_book_id]['payable_date'] = self._int_to_date(
                        dividend['payable_date'][0]
                    )
                except ValueError:
                    self._dividend_receivable[order_book_id]['payable_date'] = self._int_to_date(
                        dividend['ex_dividend_date'][0]
                    )

    def _handle_split(self, trading_date):
        data_proxy = Environment.get_instance().data_proxy
        for order_book_id, position in six.iteritems(self._positions):
            ratio = data_proxy.get_split_by_ex_date(order_book_id, trading_date)
            if ratio is None:
                continue
            position.split_(ratio)

    def _handle_transform(self):
        if not self._pending_transform:
            return
        for predecessor, (successor, conversion_ratio) in six.iteritems(self._pending_transform):
            predecessor_position = self._positions.pop(predecessor)

            self._apply_trade(Trade.__from_create__(
                order_id=None,
                price=predecessor_position.avg_price / conversion_ratio,
                amount=predecessor_position.quantity * conversion_ratio,
                side=SIDE.BUY,
                position_effect=POSITION_EFFECT.OPEN,
                order_book_id=successor
            ))
            user_system_log.warn(_(u"{predecessor} code has changed to {successor}, change position by system").format(
                predecessor=predecessor, successor=successor))

        self._pending_transform.clear()

    @property
    def dividend_receivable(self):
        """
        [float] 投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分
        """
        return sum(d['quantity'] * d['dividend_per_share'] for d in six.itervalues(self._dividend_receivable))

    @property
    def total_value(self):
        """
        [float] 股票账户总权益

        股票账户总权益 = 股票账户总资金 + 股票持仓总市值 + 应收分红

        """
        return super(StockAccount, self).total_value + self.dividend_receivable
