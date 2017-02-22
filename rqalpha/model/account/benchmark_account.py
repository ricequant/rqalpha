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
import numpy as np

from .base_account import BaseAccount
from ..dividend import Dividend
from ...execution_context import ExecutionContext
from ...const import ACCOUNT_TYPE


class BenchmarkAccount(BaseAccount):
    def __init__(self, env, init_cash, start_date):
        super(BenchmarkAccount, self).__init__(env, init_cash, start_date, ACCOUNT_TYPE.BENCHMARK)
        self.benchmark = env.config.base.benchmark

    def before_trading(self):
        portfolio = self.portfolio
        portfolio._yesterday_portfolio_value = portfolio.portfolio_value
        trading_date = ExecutionContext.get_current_trading_dt().date()
        self._handle_dividend_payable(trading_date)

    def bar(self, bar_dict):
        price = bar_dict[self.config.base.benchmark].close
        if np.isnan(price):
            return
        portfolio = self.portfolio
        portfolio._portfolio_value = None
        position = portfolio.positions[self.benchmark]

        if portfolio.market_value == 0:
            trade_quantity = int(portfolio.cash / price)
            delta_value = trade_quantity * price
            commission = 0.0008 * trade_quantity * price
            position._total_commission = commission
            position._buy_trade_quantity = trade_quantity
            position._buy_trade_value = delta_value
            position._market_value = delta_value
            portfolio._cash = portfolio._cash - delta_value - commission
        else:
            position._market_value = position._buy_trade_quantity * price

    def after_trading(self):
        trading_date = ExecutionContext.get_current_trading_dt().date()
        self.portfolio_persist()
        self._handle_dividend_ex_dividend(trading_date)

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
                    # user_log.info(_("get dividend {dividend} for {order_book_id}").format(
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
                'book_closure_date': dividend_series['book_closure_date'],
                'ex_dividend_date': dividend_series['ex_dividend_date'],
                'payable_date': dividend_series['payable_date'],
                'dividend_cash_before_tax': dividend_series['dividend_cash_before_tax'],
                'round_lot': dividend_series['round_lot']
            }

            dividend_per_share = dividend_series_dict["dividend_cash_before_tax"] / dividend_series_dict["round_lot"]
            self.portfolio._dividend_info[order_book_id] = Dividend(order_book_id, position._quantity, dividend_series_dict)
            self.portfolio._dividend_receivable += dividend_per_share * position._quantity
