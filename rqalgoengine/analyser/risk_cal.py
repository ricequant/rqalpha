# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

from .risk import Risk


class RiskCal(object):
    def __init__(self, trading_env):
        self.trading_days_a_year = 252
        self.trading_index = trading_env.trading_calendar
        self.trading_days_cnt = len(self.trading_index)

        self.strategy_total_daily_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_total_daily_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_daily_returns = None
        self.benchmark_current_daily_returns = None

        self.strategy_total_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_total_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_total_returns = None
        self.benchmark_current_total_returns = None

        self.risk = Risk()

        self.current_max_returns = -np.inf
        self.current_max_drawdown = 0

    def calculate(self, date, strategy_daily_returns, benchmark_daily_returns):
        idx = self.latest_idx = self.trading_index.get_loc(date)

        self.strategy_total_daily_returns[idx] = strategy_daily_returns
        self.benchmark_total_daily_returns[idx] = benchmark_daily_returns
        self.strategy_current_daily_returns = self.strategy_total_daily_returns[:idx + 1]
        self.benchmark_current_daily_returns = self.benchmark_total_daily_returns[:idx + 1]

        self.strategy_total_returns[idx] = (1. + self.strategy_current_daily_returns).prod() - 1
        self.benchmark_total_returns[idx] = (1. + self.benchmark_current_daily_returns).prod() - 1
        self.strategy_current_total_returns = self.strategy_total_returns[:idx + 1]
        self.benchmark_current_total_returns = self.benchmark_total_returns[:idx + 1]

        if self.strategy_current_total_returns[-1] > self.current_max_returns:
            self.current_max_returns = self.strategy_current_total_returns[-1]

        risk = self.risk
        risk.volatility = self.cal_volatility()
        risk.max_drawdown = self.cal_max_drawdown()

    def cal_volatility(self):
        daily_returns = self.strategy_current_daily_returns
        volatility = self.trading_days_a_year ** 0.5 * np.std(daily_returns, ddof=1)
        return volatility

    def cal_max_drawdown(self):
        today_return = self.strategy_current_total_returns[-1]
        today_drawdown = (1. + today_return) / (1. + self.current_max_returns) - 1.
        if today_drawdown < self.current_max_drawdown:
             self.current_max_drawdown = today_drawdown
        return self.current_max_drawdown
