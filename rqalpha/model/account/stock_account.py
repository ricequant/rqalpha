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
import pandas as pd

from .base_account import BaseAccount
from ..dividend import Dividend
from ...const import SIDE, ACCOUNT_TYPE
from ...utils.i18n import gettext as _
from ...utils.logger import user_system_log, system_log
from ...execution_context import ExecutionContext


class StockAccount(BaseAccount):
    def __init__(self, env, init_cash, start_date):
        super(StockAccount, self).__init__(env, init_cash, start_date, ACCOUNT_TYPE.STOCK)

    def before_trading(self):
        super(StockAccount, self).before_trading()
        positions = self.portfolio.positions
        removing_ids = []
        for order_book_id in positions.keys():
            position = positions[order_book_id]
            if position._quantity == 0:
                removing_ids.append(order_book_id)
        for order_book_id in removing_ids:
            positions.pop(order_book_id, None)
        trading_date = ExecutionContext.get_current_trading_dt().date()
        self._handle_dividend_payable(trading_date)
        if self.config.base.handle_split:
            self._handle_split(trading_date)

    def after_trading(self):
        trading_date = ExecutionContext.get_current_trading_dt().date()
        portfolio = self.portfolio
        # de_listed may occur
        portfolio._portfolio_value = None

        positions = portfolio.positions

        de_listed_id_list = []
        # update buy_today_holding_quantity to zero for T+1
        for order_book_id in positions:
            position = positions[order_book_id]
            position._buy_today_holding_quantity = 0

            # 检查股票今天是否退市，如果退市，则按照close_price卖出，并warning
            if position._de_listed_date is not None and trading_date >= position._de_listed_date.date():
                de_listed_id_list.append(order_book_id)

        for de_listed_id in de_listed_id_list:
            position = positions[de_listed_id]
            if self.config.validator.cash_return_by_stock_delisted:
                portfolio._cash += position.market_value
            if position._quantity != 0:
                user_system_log.warn(
                    _("{order_book_id} is expired, close all positions by system").format(order_book_id=de_listed_id))
            del positions[de_listed_id]

    def settlement(self):
        portfolio = self.portfolio
        trading_date = ExecutionContext.get_current_trading_dt().date()

        self.portfolio_persist()

        portfolio._yesterday_portfolio_value = portfolio.portfolio_value

        self._handle_dividend_ex_dividend(trading_date)

    def bar(self, bar_dict):
        portfolio = self.portfolio
        # invalidate cache
        portfolio._portfolio_value = None
        positions = portfolio.positions

        for order_book_id, position in six.iteritems(positions):
            bar = bar_dict[order_book_id]
            if not bar.isnan:
                position._market_value = position._quantity * bar.close
                position._last_price = bar.close

    def tick(self, tick):
        portfolio = self.portfolio
        # invalidate cache
        portfolio._portfolio_value = None
        position = portfolio.positions[tick.order_book_id]

        position._market_value = position._quantity * tick.last_price
        position._last_price = tick.last_price

    def order_pending_new(self, account, order):
        if self != account:
            return
        if order._is_final():
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        position._total_orders += 1
        create_quantity = order.quantity
        create_value = order._frozen_price * create_quantity

        self._update_order_data(order, create_quantity, create_value)
        self._update_frozen_cash(order, create_value)

    def order_creation_pass(self, account, order):
        pass

    def order_creation_reject(self, account, order):
        if self != account:
            return
        order_book_id = order.order_book_id
        position = self.portfolio.positions[order_book_id]
        position._total_orders += 1
        cancel_quantity = order.unfilled_quantity
        cancel_value = order._frozen_price * cancel_quantity
        self._update_order_data(order, cancel_quantity, cancel_value)
        self._update_frozen_cash(order, -cancel_value)

    def order_pending_cancel(self, account, order):
        pass

    def order_cancellation_pass(self, account, order):
        if self != account:
            return
        canceled_quantity = order.unfilled_quantity
        canceled_value = order._frozen_price * canceled_quantity
        self._update_order_data(order, -canceled_quantity, -canceled_value)
        self._update_frozen_cash(order, -canceled_value)

    def order_cancellation_reject(self, account, order):
        pass

    def trade(self, account, trade):
        if self != account:
            return
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        order = trade.order
        bar_dict = ExecutionContext.get_current_bar_dict()
        order_book_id = order.order_book_id
        position = portfolio.positions[order.order_book_id]
        position._is_traded = True
        trade_quantity = trade.last_quantity
        minus_value_by_trade = order._frozen_price * trade_quantity
        trade_value = trade.last_price * trade_quantity

        if order.side == SIDE.BUY:
            position._avg_price = (position._avg_price * position._quantity +
                                   trade_quantity * trade.last_price) / (position._quantity + trade_quantity)

        self._update_order_data(order, -trade_quantity, -minus_value_by_trade)
        self._update_trade_data(order, trade, trade_quantity, trade_value)
        self._update_frozen_cash(order, -minus_value_by_trade)
        price = bar_dict[order_book_id].close
        if order.side == SIDE.BUY and order.order_book_id not in \
                {'510900.XSHG', '513030.XSHG', '513100.XSHG', '513500.XSHG'}:
            position._buy_today_holding_quantity += trade_quantity
        position._market_value = (position._buy_trade_quantity - position._sell_trade_quantity) * price
        position._last_price = price
        position._total_trades += 1

        portfolio._total_tax += trade.tax
        portfolio._total_commission += trade.commission
        portfolio._cash = portfolio._cash - trade.tax - trade.commission
        if order.side == SIDE.BUY:
            portfolio._cash -= trade_value
        else:
            portfolio._cash += trade_value

    def order_unsolicited_update(self, account, order):
        if self != account:
            return
        rejected_quantity = order.unfilled_quantity
        rejected_value = order._frozen_price * rejected_quantity
        self._update_order_data(order, -rejected_quantity, -rejected_value)
        self._update_frozen_cash(order, -rejected_value)

    def _update_order_data(self, order, inc_order_quantity, inc_order_value):
        position = self.portfolio.positions[order.order_book_id]
        if order.side == SIDE.BUY:
            position._buy_order_quantity += inc_order_quantity
            position._buy_order_value += inc_order_value
        else:
            position._sell_order_quantity += inc_order_quantity
            position._sell_order_value += inc_order_value

    def _update_trade_data(self, order, trade, trade_quantity, trade_value):
        position = self.portfolio.positions[order.order_book_id]
        position._transaction_cost = position._transaction_cost + trade.commission + trade.tax
        if order.side == SIDE.BUY:
            position._buy_trade_quantity += trade_quantity
            position._buy_trade_value += trade_value
        else:
            position._sell_trade_quantity += trade_quantity
            position._sell_trade_value += trade_value

    def _update_frozen_cash(self, order, inc_order_value):
        portfolio = self.portfolio
        if order.side == SIDE.BUY:
            portfolio._frozen_cash += inc_order_value
            portfolio._cash -= inc_order_value

    def _handle_split(self, trading_date):
        import rqdatac
        for order_book_id, position in six.iteritems(self.portfolio.positions):
            split_df = rqdatac.get_split(order_book_id, start_date="2005-01-01", end_date="2099-01-01")
            if split_df is None:
                system_log.warn("no split data {}", order_book_id)
                continue
            try:
                series = split_df.loc[trading_date]
            except KeyError:
                continue

            # 处理拆股

            user_system_log.info(_("split {order_book_id}, {position}").format(
                order_book_id=order_book_id,
                position=position,
            ))

            ratio = series.split_coefficient_to / series.split_coefficient_from
            for key in ["_buy_order_quantity", "_sell_order_quantity", "_buy_trade_quantity", "_sell_trade_quantity"]:
                setattr(position, key, getattr(position, key) * ratio)

            user_system_log.info(_("split {order_book_id}, {position}").format(
                order_book_id=order_book_id,
                position=position,
            ))

            user_system_log.info(_("split {order_book_id}, {series}").format(
                order_book_id=order_book_id,
                series=series,
            ))

    def _handle_dividend_payable(self, trading_date):
        """handle dividend payable before trading
        """
        to_delete_dividend = []
        for order_book_id, dividend_info in six.iteritems(self.portfolio._dividend_info):
            dividend_series_dict = dividend_info.dividend_series_dict

            if pd.Timestamp(trading_date) == pd.Timestamp(dividend_series_dict['payable_date']):
                dividend_per_share = dividend_series_dict["dividend_cash_before_tax"] / dividend_series_dict["round_lot"]
                if dividend_per_share > 0 and dividend_info.quantity > 0:
                    dividend_cash = dividend_per_share * dividend_info.quantity
                    self.portfolio._dividend_receivable -= dividend_cash
                    self.portfolio._cash += dividend_cash
                    # user_system_log.info(_("get dividend {dividend} for {order_book_id}").format(
                    #     dividend=dividend_cash,
                    #     order_book_id=order_book_id,
                    # ))
                    to_delete_dividend.append(order_book_id)

        for order_book_id in to_delete_dividend:
            self.portfolio._dividend_info.pop(order_book_id, None)

    def _handle_dividend_ex_dividend(self, trading_date):
        data_proxy = ExecutionContext.get_data_proxy()
        for order_book_id, position in six.iteritems(self.portfolio.positions):
            dividend_series = data_proxy.get_dividend_by_book_date(order_book_id, trading_date)
            if dividend_series is None:
                continue

            dividend_series_dict = {
                'book_closure_date': dividend_series['book_closure_date'].to_pydatetime(),
                'ex_dividend_date': dividend_series['ex_dividend_date'].to_pydatetime(),
                'payable_date': dividend_series['payable_date'].to_pydatetime(),
                'dividend_cash_before_tax': float(dividend_series['dividend_cash_before_tax']),
                'round_lot': int(dividend_series['round_lot'])
            }

            dividend_per_share = dividend_series_dict["dividend_cash_before_tax"] / dividend_series_dict["round_lot"]

            self.portfolio._dividend_info[order_book_id] = Dividend(order_book_id, position._quantity, dividend_series_dict)
            self.portfolio._dividend_receivable += dividend_per_share * position._quantity
