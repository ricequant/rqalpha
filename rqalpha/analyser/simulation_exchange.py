# -*- coding: utf-8 -*-

import copy
from collections import defaultdict, OrderedDict

import pandas as pd
import numpy as np
from six import iteritems

from .. import const
from ..account import Account
from ..data import BarMap
from ..i18n import gettext as _
from ..logger import user_log
from ..utils.context import ExecutionContext
from .commission import AStockCommission
from .slippage import FixedPercentSlippageDecider
from .tax import AStockTax
from .order import Order
from .order_style import MarketOrder, LimitOrder
from .portfolio import Portfolio
from .position import Position
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
        self.account = Account(start_date=start_date)

        self.benchmark_portfolio_value = None

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
        self.handle_dividend()

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
        if self.benchmark_portfolio_value is None:
            self.benchmark_portfolio_value = self.data_proxy.get_bar(
                self.trading_params.benchmark, pd.Timestamp(self.start_date)).close

        new_benchmark_portfolio_value = self.data_proxy.get_bar(
            self.trading_params.benchmark, pd.Timestamp(self.current_date)).close
        benchmark_daily_returns = new_benchmark_portfolio_value / self.benchmark_portfolio_value - 1
        self.benchmark_portfolio_value = new_benchmark_portfolio_value

        self.risk_cal.calculate(self.current_date, portfolio.daily_returns, benchmark_daily_returns)

    def get_yesterday_portfolio(self):
        return self.daily_portfolios.get(self.last_date)

    def reject_all_open_orders(self):
        for order_book_id, order_list in iteritems(self.open_orders):
            for order in order_list:
                order.mark_rejected(_("market close"))
            del order_list[:]

    def on_bar_close(self, bar_dict):
        trades, close_orders = self.match_orders(bar_dict)

        for trade in trades:
            self.account.record_new_trade(self.current_date, trade)

        self.remove_close_orders(close_orders)

        self.update_portfolio_on_bar_close(bar_dict)

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

    def update_portfolio_on_bar_close(self, bar_dict):
        portfolio = self.account.portfolio
        positions = portfolio.positions

        for order_book_id, position in iteritems(positions):
            position.market_value = position.quantity * bar_dict[order_book_id].close

        portfolio.market_value = sum(position.market_value for order_book_id, position in iteritems(positions))
        portfolio.portfolio_value = portfolio.market_value + portfolio.cash

        for order_book_id, position in iteritems(positions):
            position.value_percent = position.market_value / portfolio.portfolio_value

    def create_order(self, order_book_id, amount, style):
        if style is None:
            style = MarketOrder()

        order = Order(self.dt, order_book_id, amount, style)

        self.open_orders[order_book_id].append(order)
        self.all_orders[order.order_id] = order

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

        # handle limit order
        if self.trading_params.frequency == "1d":
            if isinstance(order.style, LimitOrder):
                limit_price = order.style.get_limit_price(is_buy)
                if is_buy and limit_price < bar.close:
                    return False, _("Order Rejected: price is to low to buy {order_book_id}").format(
                        order_book_id=order_book_id)
                elif not is_buy and limit_price > bar.close:
                    return False, _("Order Rejected: price is to high to sell {order_book_id}").format(
                        order_book_id=order_book_id)
        else:
            raise NotImplementedError

        # check amount
        if abs(amount) < 100:
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

        # TODO check whether is enough to sell
        if order.quantity < 0 and abs(order.quantity) > position.sellable:
            return False, _("Order Rejected: no enough stock {order_book_id} to sell, you want to sell {quantity}, sellable {sellable}").format(
                order_book_id=order_book_id,
                quantity=abs(order.quantity),
                sellable=position.sellable,
            )

        # check whether is trading
        # FIXME need a better solution
        if bar.volume == 0:
            return False, _("Order Rejected: {order_book_id} is not trading.").format(
                order_book_id=order_book_id,
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

    def handle_dividend(self):
        data_proxy = self.data_proxy
        portfolio = self.account.portfolio
        for order_book_id, position in iteritems(portfolio.positions):
            dividend_per_share = data_proxy.get_dividend_per_share(order_book_id, self.current_date)
            if dividend_per_share > 0 and position.quantity > 0:
                dividend = dividend_per_share * position.quantity
                portfolio.cash += dividend
                user_log.info(_("get dividend {dividend} for {order_book_id}").format(
                    dividend=dividend,
                    order_book_id=order_book_id,
                ))
