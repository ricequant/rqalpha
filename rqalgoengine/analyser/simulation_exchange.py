# -*- coding: utf-8 -*-

import copy
from collections import defaultdict, OrderedDict

from six import iteritems

from ..utils.context import ExecutionContext
from ..logger import user_log
from .position import Position
from .portfolio import Portfolio
from .order_style import MarketOrder, LimitOrder
from .order import Order
from .trade import Trade
from ..data import BarMap, RqDataProxy
from .portfolio_manager import PortfolioManager
from ..i18n import gettext as _


class SimuExchange(object):
    def __init__(self, data_proxy, trading_env, **kwargs):
        self.data_proxy = data_proxy
        self.trading_env = trading_env

        self.all_orders = {}
        self.open_orders = defaultdict(list)
        # self.pending_orders = {}
        self.dt = None
        self.trades = defaultdict(list)

        self.positions = defaultdict(Position)
        self.portfolio = portfolio = Portfolio()

        self.daily_portfolios = OrderedDict()

        self.strategy = None

        portfolio.cash = portfolio.starting_cash = kwargs.get("init_cash", 100000.)
        portfolio.positions = self.positions
        portfolio.start_date = trading_env.trading_calendar[0].date()

        self.last_date = None
        self.simu_days = 0
        self.days_a_year = 365

    def set_strategy(self, strategy):
        self.strategy = strategy

    def on_dt_change(self, dt):
        if dt.date() != self.current_date:
            self.last_date = self.current_date

        self.dt = dt

    @property
    def current_date(self):
        return self.dt.date() if self.dt else None

    def on_day_close(self):
        self.simu_days += 1

        self.reject_all_open_orders()

        # from ipdb import set_trace ; set_trace()

        trades = self.trades[self.current_date]

        # update position sellable for T+1
        for trade in trades:
            position = self.positions[trade.order_book_id]
            position.sellable += trade.amount

        self.update_daily_portfolio()

        # store today portfolio
        self.daily_portfolios[self.current_date] = copy.deepcopy(self.portfolio)

    def get_yesterday_portfolio(self):
        return self.daily_portfolios.get(self.last_date)


    def reject_all_open_orders(self):
        for order_book_id, order_list in iteritems(self.open_orders):
            for order in order_list:
                order.mark_rejected(_("market close"))
            order_list.clear()

    def on_bar_close(self, bar_dict):
        trades, close_orders = self.match_orders(bar_dict)

        # from ipdb import set_trace ; set_trace()

        self.remove_close_orders(close_orders)

        self.update_portfolio(bar_dict)

    def update_daily_portfolio(self):
        yesterday_portfolio = self.get_yesterday_portfolio()
        portfolio = self.portfolio

        if yesterday_portfolio is None:
            yesterday_portfolio_value = portfolio.starting_cash
        else:
            yesterday_portfolio_value = yesterday_portfolio.portfolio_value

        portfolio.pnl = portfolio.portfolio_value - yesterday_portfolio_value
        portfolio.total_returns = portfolio.portfolio_value / portfolio.starting_cash - 1
        portfolio.annualized_returns = (1 + portfolio.total_returns) ** (self.days_a_year / float((self.current_date - portfolio.start_date).days + 1)) - 1

    def update_portfolio(self, bar_dict):
        portfolio = self.portfolio
        positions = portfolio.positions

        portfolio.market_value = sum(
            position.quantity * bar_dict[order_book_id].close
            for order_book_id, position in iteritems(positions)
        )
        portfolio.portfolio_value = portfolio.market_value + portfolio.cash

        # TODO cal remain fields
        portfolio.pnl = 0

    def create_order(self, order_book_id, amount, style):
        if style is None:
            style = MarketOrder()

        order = Order(self.dt, order_book_id, amount, style)

        self.open_orders[order_book_id].append(order)
        self.all_orders[order.order_id] = order

        return order

    def remove_close_orders(self, close_orders):
        for order in close_orders:
            order_list = self.open_orders[order.order_book_id]
            try:
                order_list.remove(order)
            except ValueError:
                pass

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        if order in self.open_orders[order.order_book_id]:
            order.cancel()

    def get_order(self, order_id):
        return self.all_orders[order_id]

    def match_orders(self, bar_dict):
        # TODO abstract Matching Engine
        trades = []
        close_orders = []

        portfolio = self.portfolio
        slippage_decider = self.strategy.slippage_decider
        commission_decider = self.strategy.commission_decider
        tax_decider = self.strategy.tax_decider
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

                # TODO consider commission and slippage

                trade = Trade(
                    date=order.dt,
                    order_book_id=order_book_id,
                    price=trade_price,
                    amount=order.quantity,
                    order_id=order.order_id,
                    commission=None,
                )

                commission = commission_decider.get_commission(order, trade)
                trade.commission = commission

                tax = tax_decider.get_tax(order, trade)
                trade.tax = tax

                portfolio.cash -= trade_price * amount

                portfolio.cash -= commission
                portfolio.cash -= tax

                portfolio.total_commission += commission
                portfolio.total_tax += tax

                # update order
                # TODO simu to create more trades
                order.filled_shares = order.quantity

                close_orders.append(order)
                trades.append(trade)

                # store new trade
                self.trades[self.current_date].append(trade)

                # update position
                position = self.positions[order_book_id]
                position.quantity += trade.amount

                # TODO handle Dividend

        return trades, close_orders

    def validate_order(self, bar_dict, order):
        # TODO need to be abstract as a validator

        order_book_id = order.order_book_id
        amount = order.quantity
        price = self.strategy.slippage_decider.get_trade_price(self.data_proxy, order)
        cost_money = price * amount

        # check amount
        if abs(amount) < 100:
            return False, _("Order Rejected: amount must over 100 for {order_book_id} ").format(
                order_book_id=order_book_id,
                )

        # check money is enough
        if cost_money > self.portfolio.cash:
            return False, _("Order Rejected: no enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}").format(
                order_book_id=order_book_id,
                cost_money=cost_money,
                cash=self.portfolio.cash,
                )

        # check whether is enough to sell
        position = self.positions[order_book_id]

        # from ipdb import set_trace ; set_trace()

        if order.quantity < 0 and abs(order.quantity) > position.sellable:
            return False, _("Order Rejected: no enough stock {order_book_id} to sell, you want to sell {quantity}, sellable {sellable}").format(
                order_book_id=order_book_id,
                quantity=abs(order.quantity),
                sellable=position.sellable,
                )

        # TODO check price low and high

        # TODO check whether is trading

        # TODO check whether is limit up or limit down

        # TODO check volume is over 25%

        return True, None
