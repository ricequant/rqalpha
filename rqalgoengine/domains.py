# -*- coding: utf-8 -*-


class Position(object):

    def __init__(self):
        self.quantity = 0.0
        self.bought_quantity = 0.0
        self.sold_quantity = 0.0
        self.bought_value = 0.0
        self.sold_value = 0.0
        self.total_orders = 0.0
        self.total_trades = 0.0
        self.sellable = 0.0
        self.average_cost = 0.0


class Portfolio(object):

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


class Instrument(object):

    def __init__(self):

        self.order_book_id = ""
        self.symbol = ""
        self.abbrev_symbol = ""
        self.round_lot = ""
        self.sector_name = ""
        self.industry_code = ""
        self.industry_name = ""
        self.type = ""

    @property
    def board_type(self):
        pass

    @property
    def sector_code(self):
        pass

    @property
    def listing(self):
        pass

    @property
    def listed_date(self):
        pass

    @property
    def maturity_date(self):
        pass

    @property
    def is_st(self):
        return "ST" in self.symbol

    def __str__(self):
        return self.order_book_id


class Order(object):

    def __init__(self):
        self.filled_shares = 0.0
        self.quantity = 0.0
        self.reject_reason = ""

    @property
    def order_id(self):
        return 0

    @property
    def instrument(self):
        return None

    def cancel(self):
        pass
