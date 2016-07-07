# -*- coding: utf-8 -*-


class PortfolioCal(object):

    def __init__(self):
        self.starting_cash = 0.0
        self.cash = 0.0
        self.total_returns = 0.0
        self.daily_returns = 0.0
        self.market_value = 0.0
        self.portfolio_value = 0.0
        self.pnl = 0.0
        self.dividend_receivable = 0.0
        self.annualized_returns = 0.0
        self.positions = {}
        self.start_date = None
