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

from ..margin import Margin
from ...const import SIDE, POSITION_EFFECT, ACCOUNT_TYPE
from ...utils.i18n import gettext as _
from ...utils.logger import user_system_log
from ...execution_context import ExecutionContext

from .base_account import BaseAccount


class FutureAccount(BaseAccount):
    def __init__(self, env, init_cash, start_date):
        super(FutureAccount, self).__init__(env, init_cash, start_date, ACCOUNT_TYPE.FUTURE)
        self._margin_decider = Margin(env.config.base.margin_multiplier)

    @property
    def margin_decider(self):
        return self._margin_decider

    def before_trading(self):
        super(FutureAccount, self).before_trading()
        positions = self.portfolio.positions
        removing_ids = []
        for order_book_id in positions.keys():
            position = positions[order_book_id]
            if position._quantity == 0 and position._buy_open_order_quantity == 0 \
                    and position._sell_open_order_quantity == 0:
                removing_ids.append(order_book_id)
        for order_book_id in removing_ids:
            positions.pop(order_book_id, None)

    def after_trading(self):
        pass

    def settlement(self):
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        positions = portfolio.positions
        data_proxy = ExecutionContext.get_data_proxy()
        trading_date = ExecutionContext.get_current_trading_dt().date()

        for order_book_id, position in six.iteritems(positions):
            settle_price = data_proxy.get_settle_price(order_book_id, trading_date)
            position._last_price = settle_price
            self._update_market_value(position, settle_price)

        self.portfolio_persist()

        portfolio._yesterday_portfolio_value = portfolio.portfolio_value

        de_listed_id_list = []
        for order_book_id, position in six.iteritems(positions):
            # 检查合约是否到期,如果到期,则按照结算价来进行平仓操作
            if position._de_listed_date is not None and trading_date >= position._de_listed_date.date():
                de_listed_id_list.append(order_book_id)
            else:
                settle_price = data_proxy.get_settle_price(order_book_id, trading_date)
                self._update_holding_by_settle(position, settle_price)
                position._daily_realized_pnl = 0
                position._buy_daily_realized_pnl = 0
                position._sell_daily_realized_pnl = 0
        for de_listed_id in de_listed_id_list:
            if positions[de_listed_id]._quantity != 0:
                user_system_log.warn(
                    _("{order_book_id} is expired, close all positions by system").format(order_book_id=de_listed_id))
            del positions[de_listed_id]

        portfolio._daily_transaction_cost = 0

    def bar(self, bar_dict):
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        positions = portfolio.positions

        for order_book_id, position in six.iteritems(positions):
            bar = bar_dict[order_book_id]
            if not bar.isnan:
                position._last_price = bar.close
                self._update_market_value(position, bar.close)

    def tick(self, tick):
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        position = portfolio.positions[tick.order_book_id]
        position._last_price = tick.last
        self._update_market_value(position, tick.last)

    def order_pending_new(self, account, order):
        if self != account:
            return
        if order._is_final():
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        position._total_orders += 1
        created_quantity = order.quantity
        created_value = order._frozen_price * created_quantity * position._contract_multiplier
        frozen_margin = self.margin_decider.cal_margin(order_book_id, order.side, created_value)
        self._update_order_data(position, order, created_quantity, created_value)
        self._update_frozen_cash(order, frozen_margin)

    def on_order_creation_pass(self, account, order):
        pass

    def order_creation_reject(self, account, order):
        if self != account:
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        cancel_quantity = order.unfilled_quantity
        cancel_value = -order._frozen_price * cancel_quantity * position._contract_multiplier
        frozen_margin = self.margin_decider.cal_margin(order_book_id, order.side, cancel_value)
        self._update_order_data(position, order, -cancel_quantity, cancel_value)
        self._update_frozen_cash(order, frozen_margin)

    def order_pending_cancel(self, account, order):
        pass

    def order_cancellation_pass(self, account, order):
        if self != account:
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        canceled_quantity = order.unfilled_quantity
        canceled_value = -order._frozen_price * canceled_quantity * position._contract_multiplier
        frozen_margin = self.margin_decider.cal_margin(order_book_id, order.order_book_id, canceled_value)
        self._update_order_data(position, order, -canceled_quantity, canceled_value)
        self._update_frozen_cash(order, frozen_margin)

    def order_cancellation_reject(self, account, order):
        pass

    def trade(self, account, trade):
        if self != account:
            return
        order = trade.order
        order_book_id = order.order_book_id
        bar_dict = ExecutionContext.get_current_bar_dict()
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        position = portfolio.positions[order_book_id]
        position._is_traded = True
        position._total_trades += 1
        trade_quantity = trade.last_quantity

        if order.position_effect == POSITION_EFFECT.OPEN:
            if order.side == SIDE.BUY:
                position._buy_avg_open_price = (position._buy_avg_open_price * position.buy_quantity + trade_quantity *
                                                trade.last_price) / (position.buy_quantity + trade_quantity)
            elif order.side == SIDE.SELL:
                position._sell_avg_open_price = (position._sell_avg_open_price * position.sell_quantity +
                                                 trade_quantity * trade.last_price) / (position.sell_quantity +
                                                                                  trade_quantity)

        minus_value_by_trade = -order._frozen_price * trade_quantity * position._contract_multiplier
        trade_value = trade.last_price * trade_quantity * position._contract_multiplier
        frozen_margin = self.margin_decider.cal_margin(order_book_id, order.side, minus_value_by_trade)

        portfolio._total_tax += trade.tax
        portfolio._total_commission += trade.commission
        portfolio._daily_transaction_cost = portfolio._daily_transaction_cost + trade.tax + trade.commission

        self._update_frozen_cash(order, frozen_margin)
        self._update_order_data(position, order, -trade_quantity, minus_value_by_trade)
        self._update_trade_data(position, trade, trade_quantity, trade_value)

        self._update_market_value(position, bar_dict[order_book_id].close)

    def order_unsolicited_update(self, account, order):
        if self != account:
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order.order_book_id]
        rejected_quantity = order.unfilled_quantity
        rejected_value = -order._frozen_price * rejected_quantity * position._contract_multiplier
        frozen_margin = self.margin_decider.cal_margin(order_book_id, order.side, rejected_value)
        self._update_order_data(position, order, -rejected_quantity, rejected_value)
        self._update_frozen_cash(order, frozen_margin)

    @staticmethod
    def _update_holding_by_settle(position, settle_price):
        position._prev_settle_price = settle_price
        position._buy_old_holding_list += position._buy_today_holding_list
        position._sell_old_holding_list += position._sell_today_holding_list
        position._buy_today_holding_list = []
        position._sell_today_holding_list = []

    def _update_trade_data(self, position, trade, trade_quantity, trade_value):
        """
        计算 [buy|sell]_trade_[value|quantity]
        计算 [buy|sell]_[open|close]_trade_quantity
        计算 [buy|sell]_settle_holding
        计算 [buy|sell]_today_holding_list
        计算 [buy|sell]_holding_cost
        计算 [bar|sell]_margin
        计算 daily_realized_pnl
        """
        order = trade.order

        if order.side == SIDE.BUY:
            if order.position_effect == POSITION_EFFECT.OPEN:
                position._buy_open_trade_quantity += trade_quantity
                position._buy_open_trade_value += trade_value
                position._buy_open_transaction_cost += trade.commission
                position._buy_today_holding_list.insert(0, (trade.last_price, trade_quantity))
            else:
                position._buy_close_trade_quantity += trade_quantity
                position._buy_close_trade_value += trade_value
                position._buy_close_transaction_cost += trade.commission
                delta_daily_realized_pnl = self._update_holding_by_close_action(trade)
                position._daily_realized_pnl += delta_daily_realized_pnl
                position._sell_daily_realized_pnl += delta_daily_realized_pnl
            position._buy_trade_quantity += trade_quantity
            position._buy_trade_value += trade_value
        else:
            if order.position_effect == POSITION_EFFECT.OPEN:
                position._sell_open_trade_quantity += trade_quantity
                position._sell_open_trade_value += trade_value
                position._sell_open_transaction_cost += trade.commission
                position._sell_today_holding_list.insert(0, (trade.last_price, trade_quantity))
            else:
                position._sell_close_trade_quantity += trade_quantity
                position._sell_close_trade_value += trade_value
                position._sell_close_transaction_cost += trade.commission
                delta_daily_realized_pnl = self._update_holding_by_close_action(trade)
                position._daily_realized_pnl += delta_daily_realized_pnl
                position._buy_daily_realized_pnl += delta_daily_realized_pnl
            position._sell_trade_quantity += trade_quantity
            position._sell_trade_value += trade_value

    @staticmethod
    def _update_order_data(position, order, inc_order_quantity, inc_order_value):
        if order.side == SIDE.BUY:
            if order.position_effect == POSITION_EFFECT.OPEN:
                position._buy_open_order_quantity += inc_order_quantity
                position._buy_open_order_value += inc_order_value
            else:
                position._buy_close_order_quantity += inc_order_quantity
                position._buy_close_order_value += inc_order_value
        else:
            if order.position_effect == POSITION_EFFECT.OPEN:
                position._sell_open_order_quantity += inc_order_quantity
                position._sell_open_order_value += inc_order_value
            else:
                position._sell_close_order_quantity += inc_order_quantity
                position._sell_close_order_value += inc_order_value

    def _update_frozen_cash(self, order, inc_order_value):
        if order.position_effect == POSITION_EFFECT.OPEN:
            self.portfolio._frozen_cash += inc_order_value

    def _update_holding_by_close_action(self, trade):
        order = trade.order
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        settle_price = position._prev_settle_price
        left_quantity = trade.last_quantity
        delta_daily_realized_pnl = 0
        if order.side == SIDE.BUY:
            # 先平昨仓
            while True:
                if left_quantity == 0:
                    break
                if len(position._sell_old_holding_list) == 0:
                    break
                oldest_price, oldest_quantity = position._sell_old_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    position._sell_old_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, settle_price, consumed_quantity)
            # 再平今仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = position._sell_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    position._sell_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, oldest_price, consumed_quantity)
        else:
            # 先平昨仓
            while True:
                if left_quantity == 0:
                    break
                if len(position._buy_old_holding_list) == 0:
                    break
                oldest_price, oldest_quantity = position._buy_old_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    position._buy_old_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, settle_price, consumed_quantity)
            # 再平今仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = position._buy_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    position._buy_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                    left_quantity = 0
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta_daily_realized_pnl += self._cal_daily_realized_pnl(trade, oldest_price, consumed_quantity)
        return delta_daily_realized_pnl

    @staticmethod
    def _update_market_value(position, price):
        """
        计算 market_value
        计算 pnl
        计算 daily_holding_pnl
        """
        botq = position._buy_open_trade_quantity
        sctq = position._sell_close_trade_quantity
        bctq = position._buy_close_trade_quantity
        sotq = position._sell_open_trade_quantity
        position._buy_market_value = (botq - sctq) * price * position._contract_multiplier
        position._sell_market_value = (bctq - sotq) * price * position._contract_multiplier
        position._market_value = position._buy_market_value + position._sell_market_value

    def _cal_daily_realized_pnl(self, trade, cost_price, consumed_quantity):
        order = trade.order
        position = self.portfolio.positions[order.order_book_id]
        if order.side == SIDE.BUY:
            return (cost_price - trade.last_price) * consumed_quantity * position._contract_multiplier
        else:
            return (trade.last_price - cost_price) * consumed_quantity * position._contract_multiplier
