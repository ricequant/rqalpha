# -*- coding: utf-8 -*-

from collections import defaultdict

from six import iteritems

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

        portfolio.cash = portfolio.starting_cash = kwargs.get("init_cash", 100000.)
        portfolio.positions = self.positions
        portfolio.start_date = trading_env.trading_calendar[0].date()

    def on_dt_change(self, dt):
        self.dt = dt

    @property
    def current_date(self):
        return self.dt.date()

    def on_day_close(self):
        self.reject_all_open_orders()

        # from ipdb import set_trace ; set_trace()

        trades = self.trades[self.current_date]

        # update position sellable for T+1
        for trade in trades:
            position = self.positions[trade.order_book_id]
            position.sellable += trade.amount

    def reject_all_open_orders(self):
        for order_book_id, order_list in iteritems(self.open_orders):
            for order in order_list:
                order.mark_rejected(_("market close"))
            order_list.clear()

    def on_bar_close(self, bar_dict):
        trades, close_orders = self.create_trades(bar_dict)

        # from ipdb import set_trace ; set_trace()

        self.remove_close_orders(close_orders)

        self.update_portfolio(bar_dict)

    def update_portfolio(self, bar_dict):
        portfolio = self.portfolio
        positions = portfolio.positions

        portfolio.market_value = sum(
            position.quantity * bar_dict[order_book_id].close
            for order_book_id, position in iteritems(positions)
        )
        portfolio.portfolio_value = portfolio.market_value + portfolio.cash
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

    def create_trades(self, bar_dict):
        trades = []
        close_orders = []

        portfolio = self.portfolio

        for order_book_id, order_list in iteritems(self.open_orders):
            # TODO handle limit order
            for order in order_list:
                # TODO check whether can match
                is_pass, reason = self.validate_order(bar_dict, order)
                if not is_pass:
                    order.mark_rejected(reason)
                    user_log.error(reason)
                    continue

                price = bar_dict[order.order_book_id].close
                amount = order.quantity
                money = price * amount

                trade = Trade(
                    date=order.dt,
                    order_book_id=order_book_id,
                    price=price,
                    amount=order.quantity,
                    order_id=order.order_id,
                    commission=None,
                )

                portfolio.cash -= money

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

                # position sellable should be update on_day_close

                # update portfofio

        return trades, close_orders

    def validate_order(self, bar_dict, order):
        order_book_id = order.order_book_id
        price = bar_dict[order_book_id].close
        # one order might has mulitple trades

        amount = order.quantity
        money = price * amount

        # check money is enough
        if money > self.portfolio.cash:
            return False, _("Your money is no enough to buy {order_book_id}, needs {money:.2f}, cash {cash:.2f}").format(
                order_book_id=order_book_id,
                money=money,
                cash=self.portfolio.cash,
                )

        # check whether is enough to sell
        position = self.positions[order_book_id]

        # from ipdb import set_trace ; set_trace()

        if order.quantity < 0 and abs(order.quantity) > position.sellable:
            return False, _("You don't have enough stock {order_book_id} to sell, you want to sell {quantity}, sellable {sellable}").format(
                order_book_id=order_book_id,
                quantity=abs(order.quantity),
                sellable=position.sellable,
                )

        # check price low and high

        return True, None
