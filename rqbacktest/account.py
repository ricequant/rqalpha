# -*- coding: utf-8 -*-

import datetime
import copy
from collections import defaultdict, OrderedDict

from .analyser.portfolio import Portfolio
from .analyser.commission import AStockCommission, BaseCommission
from .analyser.slippage import FixedPercentSlippageDecider, BaseSlippageDecider
from .analyser.tax import AStockTax


class Account(object):
    def __init__(self, **kwargs):
        self._slippage_decider = kwargs.get("slippage", FixedPercentSlippageDecider())
        self._commission_decider = kwargs.get("commission", AStockCommission())
        self._tax_decider = kwargs.get("tax", AStockTax())

        self._daily_trades = defaultdict(list)            # type: Dict[date, List[Trade]]
        self._portfolio = Portfolio()

        # init portfolio
        self._portfolio.cash = self._portfolio.starting_cash = kwargs.get("init_cash", 100000.)
        self._portfolio.portfolio_value = self._portfolio.cash
        self._portfolio.start_date = kwargs.get("start_date")

    @property
    def slippage_decider(self):
        return self._slippage_decider

    @slippage_decider.setter
    def slippage_decider(self, value):
        assert isinstance(value, BaseSlippageDecider)
        self._slippage_decider = value

    @property
    def commission_decider(self):
        return self._commission_decider

    @commission_decider.setter
    def commission_decider(self, value):
        assert isinstance(value, BaseCommission)
        self._commission_decider = value

    @property
    def tax_decider(self):
        return self._tax_decider

    @property
    def portfolio(self):
        """account portfolio
        Do not edit the results if you don't know what are you doing.

        :returns:
        :rtype: Portfolio

        """
        return self._portfolio

    def get_trades(self, date):
        return self._daily_trades[date]

    def get_all_trades(self):
        """get all trades

        :returns:
        :rtype: Dict[date, List[]]

        """
        return self._daily_trades

    def set_start_date(self, start_date):
        assert isinstance(date, datetime.date)
        self._portfolio.start_date = start_date

    def set_init_cash(self, cash):
        assert cash > 0
        self._portfolio.cash = self._portfolio.starting_cash = cash

    def record_new_trade(self, date, trade):
        """record new trade in Account

        :param datetime.date date:
        :param Trade trade:
        :returns: None
        :rtype:

        """
        self._daily_trades[date].append(trade)

    @property
    def portfolio_value(self):
        return self._portfolio.portfolio_value

    @property
    def cash(self):
        return self._portfolio.cash
