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

        self.strategy_total_avg_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_total_avg_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_total_avg_returns = None
        self.benchmark_current_total_avg_returns = None

        self.strategy_annual_avg_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_annual_avg_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_annual_avg_returns = None
        self.benchmark_current_annual_avg_returns = None

        self.risk = Risk()

        # TODO use yield curve
        self.risk_free_rate = 0.0271

        self.current_max_returns = -np.inf
        self.current_max_drawdown = 0

    def calculate(self, date, strategy_daily_returns, benchmark_daily_returns):
        idx = self.latest_idx = self.trading_index.get_loc(date)

        self.strategy_total_daily_returns[idx] = strategy_daily_returns
        self.benchmark_total_daily_returns[idx] = benchmark_daily_returns
        self.strategy_current_daily_returns = self.strategy_total_daily_returns[:idx + 1]
        self.benchmark_current_daily_returns = self.benchmark_total_daily_returns[:idx + 1]

        self.days_cnt = len(self.strategy_current_daily_returns)

        self.strategy_total_returns[idx] = (1. + self.strategy_current_daily_returns).prod() - 1
        self.benchmark_total_returns[idx] = (1. + self.benchmark_current_daily_returns).prod() - 1
        self.strategy_current_total_returns = self.strategy_total_returns[:idx + 1]
        self.benchmark_current_total_returns = self.benchmark_total_returns[:idx + 1]

        self.strategy_total_avg_returns[idx] = self.strategy_current_total_returns[-1] / self.days_cnt
        self.strategy_current_total_avg_returns = self.strategy_total_avg_returns[:idx + 1]
        self.benchmark_total_avg_returns[idx] = self.benchmark_current_total_returns[-1] / self.days_cnt
        self.benchmark_current_total_avg_returns = self.benchmark_total_avg_returns[:idx + 1]

        self.strategy_annual_avg_returns[idx] = self.strategy_current_total_avg_returns[-1] * self.trading_days_a_year
        self.strategy_current_annual_avg_returns = self.strategy_annual_avg_returns[:idx + 1]
        self.benchmark_annual_avg_returns[idx] = self.benchmark_current_total_avg_returns[-1] * self.trading_days_a_year
        self.benchmark_current_annual_avg_returns = self.benchmark_annual_avg_returns[:idx + 1]

        if self.strategy_current_total_returns[-1] > self.current_max_returns:
            self.current_max_returns = self.strategy_current_total_returns[-1]

        risk = self.risk
        risk.volatility = self.cal_volatility()
        risk.max_drawdown = self.cal_max_drawdown()
        risk.information_rate = self.cal_information_rate()
        risk.downside_risk = self.cal_downside_risk()
        risk.beta = self.cal_beta()
        risk.alpha = self.cal_alpha()

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

    def cal_information_rate(self):
        strategy_rets = self.strategy_current_annual_avg_returns[-1]
        benchmark_rets = self.benchmark_current_annual_avg_returns[-1]
        return (strategy_rets - benchmark_rets) / self.risk.volatility

    def cal_alpha(self):
        beta = self.risk.beta

        strategy_rets = self.strategy_current_annual_avg_returns[-1]
        benchmark_rets = self.benchmark_current_annual_avg_returns[-1]

        self.risk_free_rate

        alpha = strategy_rets - (self.risk_free_rate + beta * (benchmark_rets - self.risk_free_rate))
        return alpha

    def cal_beta(self):
        cov = np.cov(np.vstack([
            self.strategy_current_daily_returns,
            self.benchmark_current_daily_returns,
        ]), ddof=1)
        beta = cov[0][1] / cov[1][1]

        return beta

    def cal_downside_risk(self):
        return 0.
        # mask = self.strategy_current_total_returns < self.strategy_current_total_avg_returns
        # downside_diff = self.strategy_current_total_returns[mask] - self.strategy_current_total_avg_returns[mask]
        # if len(downside_diff) <= 1:
        #     return 0.0
        # return self.trading_days_a_year ** 0.5 * np.std(downside_diff, ddof=1)

    def __repr__(self):
        return "RiskCal({0})".format(self.__dict__)
