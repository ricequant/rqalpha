# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


import copy
import pandas as pd
from collections import defaultdict, OrderedDict
from six import iteritems

from ..const import ORDER_STATUS
from .. import const
from ..account import Account
from ..i18n import gettext as _
from ..logger import user_log
from .order import Order
from .order_style import MarketOrder, LimitOrder
from .portfolio import Portfolio, Dividend
from .risk_cal import RiskCal
from .trade import Trade


class SimuExchange(object):
    def __init__(self, data_proxy, trading_params, **kwargs):
        self.data_proxy = data_proxy
        self.trading_params = trading_params

        self.dt = None          # type: datetime.datetime current simulation datetime

        # TODO move risk cal outside this class
        self.risk_cal = RiskCal(trading_params, data_proxy)

        self.daily_portfolios = OrderedDict()      # type: Dict[str, Portfolio], each day has a portfolio copy
        self.all_orders = {}                       # type: Dict[str, Order], all orders, including cancel orders
        self.open_orders = defaultdict(list)       # type: Dict[str, List[Order]], all open orders

        self.start_date = start_date = self.trading_params.trading_calendar[0].date()
        self.account = Account(start_date=start_date, init_cash=self.trading_params.init_cash)

        # TODO should treat benchmark as a buy and hold strategy
        self.benchmark_portfolio_value = self.benchmark_cash = self.trading_params.init_cash
        self.benchmark_market_value = 0
        self.benchmark_quantity = 0

        self.last_date = None        # type: datetime.date, last trading date
        self.simu_days_cnt = 0       # type: int, days count since simulation start

    def on_dt_change(self, dt):
        if dt.date() != self.current_date:
            self.last_date = self.current_date

        self.dt = dt

    @property
    def current_date(self):
        return self.dt.date() if self.dt else None

    def on_day_open(self):
        self.handle_dividend_payable()

    def on_day_close(self):
        self.simu_days_cnt += 1

        self.reject_all_open_orders()

        trades = self.account.get_trades(self.current_date)
        portfolio = self.account.portfolio
        positions = portfolio.positions

        # update position sellable for T+1
        for trade in trades:
            position = positions[trade.order_book_id]
            position.sellable += trade.amount

        self.update_daily_portfolio()

        for order_book_id in list(positions.keys()):
            position = positions[order_book_id]
            if position.quantity == 0:
                positions.pop(order_book_id)

        # store today portfolio
        self.daily_portfolios[self.current_date] = copy.deepcopy(portfolio)

        # TODO make benchmark cal works better
        # update benchmark
        if self.benchmark_market_value == 0:
            self.benchmark_market_value = None

            origin_benchmark_portfolio_value = self.benchmark_portfolio_value

            # FIXME quick dirty hack
            price = self.data_proxy.get_bar(self.trading_params.benchmark, pd.Timestamp(self.start_date)).close
            self.benchmark_quantity = self.benchmark_portfolio_value / price
            self.benchmark_quantity = int(self.benchmark_quantity)
            trade_price = price
            commission = 0.0008 * trade_price * self.benchmark_quantity

            self.benchmark_cash -= trade_price * self.benchmark_quantity
            self.benchmark_cash -= commission

            self.benchmark_market_value = price * self.benchmark_quantity
            self.benchmark_portfolio_value = self.benchmark_market_value + self.benchmark_cash

            benchmark_daily_returns = self.benchmark_portfolio_value / origin_benchmark_portfolio_value - 1
        else:
            new_benchmark_market_value = self.data_proxy.get_bar(
                self.trading_params.benchmark, pd.Timestamp(self.current_date)).close * self.benchmark_quantity
            new_benchmark_portfolio_value = new_benchmark_market_value + self.benchmark_cash

            benchmark_daily_returns = new_benchmark_portfolio_value / self.benchmark_portfolio_value - 1
            self.benchmark_portfolio_value = new_benchmark_portfolio_value

        self.risk_cal.calculate(self.current_date, portfolio.daily_returns, benchmark_daily_returns)

        self.handle_dividend_ex_dividend()

    def get_yesterday_portfolio(self):
        return self.daily_portfolios.get(self.last_date)

    def reject_all_open_orders(self):
        for order_book_id, order_list in iteritems(self.open_orders):
            for order in order_list:
                user_log.warn(_("Order Rejected: {order_book_id} can not match, {order_list}").format(
                    order_book_id=order_book_id,
                    order_list=order_list,
                ))
                order.mark_rejected(_("market close"))
            del order_list[:]

    def match_current_orders(self, bar_dict):
        trades, close_orders = self.match_orders(bar_dict)

        for trade in trades:
            self.account.record_new_trade(self.current_date, trade)

        self.remove_close_orders(close_orders)

        # remove rejected order
        rejected_orders = []
        for order_book_id, order_list in iteritems(self.open_orders):
            for order in order_list:
                if order.status == ORDER_STATUS.REJECTED:
                    rejected_orders.append(order)

        self.remove_close_orders(rejected_orders)

    def on_bar_close(self, bar_dict):
        self.match_orders(bar_dict)
        # self.update_portfolio(bar_dict)

    def update_daily_portfolio(self):
        yesterday_portfolio = self.get_yesterday_portfolio()
        portfolio = self.account.portfolio

        if yesterday_portfolio is None:
            yesterday_portfolio_value = portfolio.starting_cash
        else:
            yesterday_portfolio_value = yesterday_portfolio.portfolio_value

        portfolio.pnl = portfolio.portfolio_value - yesterday_portfolio_value
        portfolio.daily_returns = portfolio.pnl / yesterday_portfolio_value
        portfolio.total_returns = portfolio.portfolio_value / portfolio.starting_cash - 1
        portfolio.annualized_returns = (1 + portfolio.total_returns) ** (
            const.DAYS_CNT.DAYS_A_YEAR / float((self.current_date - self.trading_params.start_date).days + 1)) - 1

    def update_portfolio(self, bar_dict):
        portfolio = self.account.portfolio
        positions = portfolio.positions

        for order_book_id, position in iteritems(positions):
            position.market_value = position.quantity * bar_dict[order_book_id].close

        portfolio.market_value = sum(position.market_value for order_book_id, position in iteritems(positions))
        portfolio.portfolio_value = portfolio.market_value + portfolio.cash

        for order_book_id, position in iteritems(positions):
            position.value_percent = position.market_value / portfolio.portfolio_value

    def create_order(self, bar_dict, order_book_id, amount, style):
        if style is None:
            style = MarketOrder()

        order = Order(self.dt, order_book_id, amount, style)

        self.open_orders[order_book_id].append(order)
        self.all_orders[order.order_id] = order

        # match order here because ricequant do this
        self.match_current_orders(bar_dict)
        self.update_portfolio(bar_dict)

        return order

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order in self.open_orders[order.order_book_id]:
            order.cancel()

    def remove_close_orders(self, close_orders):
        for order in close_orders:
            order_list = self.open_orders[order.order_book_id]
            try:
                order_list.remove(order)
            except ValueError:
                pass

    def get_order(self, order_id):
        return self.all_orders[order_id]

    def match_orders(self, bar_dict):
        # TODO abstract Matching Engine
        trades = []
        close_orders = []

        portfolio = self.account.portfolio
        positions = portfolio.positions

        slippage_decider = self.account.slippage_decider
        commission_decider = self.account.commission_decider
        tax_decider = self.account.tax_decider
        data_proxy = self.data_proxy

        for order_book_id, order_list in iteritems(self.open_orders):
            # TODO handle limit order
            for order in order_list:
                # TODO check whether can match
                is_pass, reason = self.validate_order(bar_dict, order)
                if not is_pass:
                    order.mark_rejected(reason)
                    user_log.error(reason)
                    continue

                trade_price = slippage_decider.get_trade_price(data_proxy, order)
                amount = order.quantity

                trade = Trade(
                    date=order.dt,
                    order_book_id=order_book_id,
                    price=trade_price,
                    amount=order.quantity,
                    order_id=order.order_id,
                    commission=0.,
                )

                commission = commission_decider.get_commission(order, trade)
                trade.commission = commission

                tax = tax_decider.get_tax(order, trade)
                trade.tax = tax

                # deduct available cash
                portfolio.cash -= trade_price * amount

                # cal commisssion & tax
                portfolio.cash -= commission
                portfolio.cash -= tax
                portfolio.total_commission += commission
                portfolio.total_tax += tax

                # update order
                # TODO simu to create more trades
                order.filled_shares = order.quantity

                close_orders.append(order)
                trades.append(trade)

                # update position
                position = positions[order_book_id]
                position.quantity += trade.amount

                if trade.amount > 0:
                    position.bought_quantity += trade.amount
                    position.bought_value += trade_price * amount
                else:
                    position.sold_quantity += abs(trade.amount)
                    position.sold_value += abs(trade_price * amount)

        return trades, close_orders

    def validate_order(self, bar_dict, order):
        # TODO need to be abstract as a validator

        order_book_id = order.order_book_id

        portfolio = self.account.portfolio
        positions = portfolio.positions
        position = positions[order_book_id]

        bar = bar_dict[order_book_id]

        amount = order.quantity
        close_price = bar.close
        price = self.account.slippage_decider.get_trade_price(self.data_proxy, order)
        cost_money = price * amount
        is_buy = amount > 0

        # check whether is trading
        if not bar.is_trading:
            return False, _("Order Rejected: {order_book_id} is not trading.").format(
                order_book_id=order_book_id,
            )

        # handle limit order
        if self.trading_params.frequency == "1d":
            if isinstance(order.style, LimitOrder):
                limit_price = order.style.get_limit_price(is_buy)
                if is_buy and limit_price < bar.close:
                    return False, _("Order Rejected: price is too low to buy {order_book_id}").format(
                        order_book_id=order_book_id)
                elif not is_buy and limit_price > bar.close:
                    return False, _("Order Rejected: price is too high to sell {order_book_id}").format(
                        order_book_id=order_book_id)
        else:
            raise NotImplementedError

        # check amount
        if abs(amount) < int(self.data_proxy.instrument(order_book_id).round_lot):
            return False, _("Order Rejected: amount must over 100 for {order_book_id} ").format(
                order_book_id=order_book_id,
            )

        # check money is enough
        if is_buy and close_price * amount > self.account.portfolio.cash:
            return False, _("Order Rejected: no enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                order_book_id=order_book_id,
                cost_money=cost_money,
                cash=portfolio.cash,
            )

        if order.quantity < 0 and abs(order.quantity) > position.sellable:
            return False, _("Order Rejected: no enough stock {order_book_id} to sell, you want to sell {quantity}, sellable {sellable}").format(
                order_book_id=order_book_id,
                quantity=abs(order.quantity),
                sellable=position.sellable,
            )

        # # TODO check whether is limit up or limit down
        # # FIXME need to handle ST 5%
        # last_close = self.data_proxy.history(order_book_id, 2, "1d", "close").iloc[-2]
        # if is_buy and price >= last_close * 1.1:
        #     return False, _("Order Rejected: {order_book_id} is limit up.").format(
        #         order_book_id=order_book_id,
        #         )
        # elif not is_buy and price <= last_close * 0.9:
        #     return False, _("Order Rejected: {order_book_id} is limit down.").format(
        #         order_book_id=order_book_id,
        #         )

        # TODO check volume is over 25%
        # FIXME might have mulitiple order
        if amount > bar.volume * 0.25:
            return False, _("Order Rejected: {order_book_id} volume is over 25%.").format(
                order_book_id=order_book_id,
            )

        return True, None

    def handle_dividend_ex_dividend(self):
        data_proxy = self.data_proxy
        portfolio = self.account.portfolio

        for order_book_id, position in iteritems(portfolio.positions):
            dividend_series = data_proxy.get_dividends_by_book_date(order_book_id, self.current_date)
            if dividend_series is None:
                continue
            dividend_per_share = dividend_series["dividend_cash_before_tax"] / dividend_series["round_lot"]
            portfolio._dividend_info[order_book_id] = Dividend(order_book_id, position.quantity, dividend_series)
            portfolio.dividend_receivable += dividend_per_share * position.quantity

    def handle_dividend_payable(self):
        """handle dividend payable before trading
        """
        data_proxy = self.data_proxy
        portfolio = self.account.portfolio

        to_delete_dividend = []
        for order_book_id, dividend_info in iteritems(portfolio._dividend_info):
            dividend_series = dividend_info.dividend_series

            if pd.Timestamp(self.current_date) == pd.Timestamp(dividend_series.payable_date):
                dividend_per_share = dividend_series["dividend_cash_before_tax"] / dividend_series["round_lot"]
                if dividend_per_share > 0 and dividend_info.quantity > 0:
                    dividend_cash = dividend_per_share * dividend_info.quantity
                    portfolio.dividend_receivable -= dividend_cash
                    portfolio.cash += dividend_cash
                    # user_log.info(_("get dividend {dividend} for {order_book_id}").format(
                    #     dividend=dividend_cash,
                    #     order_book_id=order_book_id,
                    # ))
                    to_delete_dividend.append(order_book_id)

        for order_book_id in to_delete_dividend:
            portfolio._dividend_info.pop(order_book_id, None)
