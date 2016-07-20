# -*- coding: utf-8 -*-
from __future__ import division
import copy
from collections import OrderedDict

import pandas as pd
import numpy as np

from .risk import Risk
from .. import const


class RiskCal(object):
    def __init__(self, trading_params, data_proxy):
        self.data_proxy = data_proxy

        self.start_date = trading_params.start_date
        self.trading_index = trading_params.trading_calendar
        self.trading_days_cnt = len(self.trading_index)

        self.strategy_total_daily_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_total_daily_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_daily_returns = None
        self.benchmark_current_daily_returns = None

        self.strategy_total_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_total_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_total_returns = None
        self.benchmark_current_total_returns = None

        self.strategy_annualized_returns = np.full(self.trading_days_cnt, np.nan)
        self.benchmark_annualized_returns = np.full(self.trading_days_cnt, np.nan)
        self.strategy_current_annualized_returns = None
        self.benchmark_current_annualized_returns = None

        self.risk = Risk()

        self.daily_risks = OrderedDict()

        self.current_max_returns = -np.inf
        self.current_max_drawdown = 0

        # FIXME might change daily?
        self.risk_free_rate = data_proxy.get_yield_curve(self.trading_index[0], self.trading_index[-1])

    def calculate(self, date, strategy_daily_returns, benchmark_daily_returns):

        idx = self.latest_idx = self.trading_index.get_loc(date)

        # daily
        self.strategy_total_daily_returns[idx] = strategy_daily_returns
        self.benchmark_total_daily_returns[idx] = benchmark_daily_returns
        self.strategy_current_daily_returns = self.strategy_total_daily_returns[:idx + 1]
        self.benchmark_current_daily_returns = self.benchmark_total_daily_returns[:idx + 1]

        self.days_cnt = len(self.strategy_current_daily_returns)
        days_pass_cnt = (date - self.start_date).days + 1

        # total
        self.strategy_total_returns[idx] = (1. + self.strategy_current_daily_returns).prod() - 1
        self.benchmark_total_returns[idx] = (1. + self.benchmark_current_daily_returns).prod() - 1
        self.strategy_current_total_returns = self.strategy_total_returns[:idx + 1]
        self.benchmark_current_total_returns = self.benchmark_total_returns[:idx + 1]

        # annual
        self.strategy_annualized_returns[idx] = (1 + self.strategy_current_total_returns[-1]) ** (
                    const.DAYS_CNT.DAYS_A_YEAR / days_pass_cnt) - 1
        self.benchmark_annualized_returns[idx] = (1 + self.benchmark_current_total_returns[-1]) ** (
            const.DAYS_CNT.DAYS_A_YEAR / days_pass_cnt) - 1
        self.strategy_current_annualized_returns = self.strategy_annualized_returns[:idx + 1]
        self.benchmark_current_annualized_returns = self.benchmark_annualized_returns[:idx + 1]

        if self.strategy_current_total_returns[-1] > self.current_max_returns:
            self.current_max_returns = self.strategy_current_total_returns[-1]

        risk = self.risk
        risk.volatility = self.cal_volatility()
        risk.max_drawdown = self.cal_max_drawdown()
        risk.tracking_error = self.cal_tracking_error()
        risk.information_rate = self.cal_information_rate(risk.volatility)
        risk.downside_risk = self.cal_downside_risk()
        risk.beta = self.cal_beta()
        risk.alpha = self.cal_alpha()
        risk.sharpe = self.cal_sharpe()
        risk.sortino = self.cal_sortino()

        self.daily_risks[date] = copy.deepcopy(risk)

    def cal_volatility(self):
        daily_returns = self.strategy_current_daily_returns
        if len(daily_returns) <= 1:
            return 0.
        volatility = const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5 * np.std(daily_returns, ddof=1)
        return volatility

    def cal_max_drawdown(self):
        today_return = self.strategy_current_total_returns[-1]
        today_drawdown = (1. + today_return) / (1. + self.current_max_returns) - 1.
        if today_drawdown < self.current_max_drawdown:
            self.current_max_drawdown = today_drawdown
        return self.current_max_drawdown

    def cal_tracking_error(self):
        diff = self.strategy_current_daily_returns - self.benchmark_current_daily_returns
        return ((diff * diff).sum() / len(diff)) ** 0.5 * const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5

    def cal_information_rate(self, volatility):
        return (self.strategy_current_annualized_returns[-1] - self.benchmark_current_annualized_returns[-1]) / volatility

    def cal_alpha(self):
        beta = self.risk.beta

        strategy_rets = self.strategy_current_annualized_returns[-1]
        benchmark_rets = self.benchmark_current_annualized_returns[-1]

        alpha = strategy_rets - (self.risk_free_rate + beta * (benchmark_rets - self.risk_free_rate))
        return alpha

    def cal_beta(self):
        if len(self.strategy_current_daily_returns) <= 1:
            return 0.
        cov = np.cov(np.vstack([
            self.strategy_current_daily_returns,
            self.benchmark_current_daily_returns,
        ]), ddof=1)
        beta = cov[0][1] / cov[1][1]

        return beta

    def cal_sharpe(self):
        volatility = self.risk.volatility
        strategy_rets = self.strategy_current_total_returns[-1]

        sharpe = (strategy_rets - self.risk_free_rate) / volatility

        return sharpe

    def cal_sortino(self):
        strategy_rets = self.strategy_current_total_returns[-1]
        downside_risk = self.risk.downside_risk

        sortino = (strategy_rets - self.risk_free_rate) / downside_risk
        return sortino

    def cal_downside_risk(self):
        mask = self.strategy_current_daily_returns < self.benchmark_current_daily_returns
        diff = self.strategy_current_daily_returns[mask] - self.benchmark_current_daily_returns[mask]
        if len(diff) <= 1:
            return 0.

        return ((diff * diff).sum() / len(diff)) ** 0.5 * const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5
        # return const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5 * np.std(diff, ddof=1)

    def __repr__(self):
        return "RiskCal({0})".format(self.__dict__)
