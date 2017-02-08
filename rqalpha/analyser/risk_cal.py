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

from __future__ import division
from collections import OrderedDict
import numpy as np
import pandas as pd
import jsonpickle

from .risk import Risk
from .. import const
from ..utils.logger import system_log


class RiskCal(object):
    def __init__(self):
        self.initialized = False

    def init(self, trading_index, is_annualized=True, save_daily_risk=True):
        self.is_annualized = is_annualized
        self.save_daily_risk = save_daily_risk

        self.date = self.start_date = None
        self.trading_index = trading_index

        self.date = self.start_date = self.trading_index[0].date()
        trading_days_cnt = len(self.trading_index)

        self.strategy_total_daily_returns = np.full(trading_days_cnt, np.nan)
        self.strategy_total_returns = np.full(trading_days_cnt, np.nan)
        self.strategy_annualized_returns = np.full(trading_days_cnt, np.nan)
        self.benchmark_total_daily_returns = np.full(trading_days_cnt, np.nan)
        self.benchmark_total_returns = np.full(trading_days_cnt, np.nan)
        self.benchmark_annualized_returns = np.full(trading_days_cnt, np.nan)

        self.strategy_current_daily_returns = self.strategy_total_daily_returns[:0]
        self.strategy_current_total_returns = self.strategy_total_returns[:0]
        self.strategy_current_annualized_returns = self.strategy_annualized_returns[:0]
        self.benchmark_current_daily_returns = self.benchmark_total_daily_returns[:0]
        self.benchmark_current_total_returns = self.benchmark_total_returns[:0]
        self.benchmark_current_annualized_returns = self.benchmark_annualized_returns[:0]

        self._risk = Risk()
        self.daily_risks = OrderedDict()

        self.current_max_returns = -np.inf
        self.current_max_drawdown = 0
        self.initialized = True

    def update_trading_index(self, trading_index):
        """PT的交易日可能会随着时间变长
        """
        if len(self.trading_index) == len(trading_index):
            return

        self.trading_index = trading_index
        size = len(self.trading_index)

        attrs = [
            "strategy_total_daily_returns", "benchmark_total_daily_returns",
            "strategy_total_returns", "benchmark_total_returns",
            "strategy_annualized_returns", "benchmark_annualized_returns",
        ]
        for attr in attrs:
            setattr(self, attr, np.resize(getattr(self, attr), (size, )))

    def calculate(self, date, strategy_daily_returns, benchmark_daily_returns, risk_free_rate):
        """calculate daily risk

        :param datetime.date date: current date
        :param float strategy_daily_returns: strategy daily return
        :param float benchmark_daily_returns: benchmark daily return
        :param float risk_free_rate: risk free period return
        :returns: today risk
        :rtype: Risk
        """
        try:
            idx = self.latest_idx = self.trading_index.get_loc(date)
        except KeyError as e:
            system_log.exception("trading_index.get_loc({}) fail", date)
            return

        self.date = date

        # daily
        self.strategy_total_daily_returns[idx] = strategy_daily_returns
        self.benchmark_total_daily_returns[idx] = benchmark_daily_returns
        self.strategy_current_daily_returns = self.strategy_total_daily_returns[:idx + 1]
        self.benchmark_current_daily_returns = self.benchmark_total_daily_returns[:idx + 1]

        self.days_cnt = len(self.strategy_current_daily_returns)
        days_pass_cnt = (date - self.start_date).days + 1

        # risk
        self.riskfree_total_returns = risk_free_rate

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

        # need to update daily
        self._risk.max_drawdown = self.cal_max_drawdown()

    @property
    def risk(self):
        risk = self._risk

        try:
            risk.volatility = self.cal_volatility()
            # risk.max_drawdown = self.cal_max_drawdown()
            risk.tracking_error = self.cal_tracking_error()
            risk.information_ratio = self.cal_information_ratio(risk.tracking_error)
            risk.downside_risk = self.cal_downside_risk()
            risk.beta = self.cal_beta()
            risk.alpha = self.cal_alpha()
            risk.sharpe = self.cal_sharpe()
            risk.sortino = self.cal_sortino()
        except Exception as e:
            system_log.exception("risk cal exc")

        if self.save_daily_risk:
            self.daily_risks[self.date] = risk._clone()
            return self.daily_risks[self.date]
        else:
            return risk._clone()

    def cal_volatility(self):
        daily_returns = self.strategy_current_daily_returns
        if len(daily_returns) <= 1:
            return 0.

        if self.is_annualized:
            volatility = const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5 * np.std(daily_returns, ddof=1)
        else:
            volatility = len(daily_returns) ** 0.5 * np.std(daily_returns, ddof=1)

        return volatility

    def cal_max_drawdown(self):
        today_return = self.strategy_current_total_returns[-1]
        today_drawdown = (1. + today_return) / (1. + self.current_max_returns) - 1.
        if today_drawdown < self.current_max_drawdown:
            self.current_max_drawdown = today_drawdown
        return abs(self.current_max_drawdown)

    def cal_tracking_error(self):
        diff = self.strategy_current_daily_returns - self.benchmark_current_daily_returns

        if self.is_annualized:
            return ((diff * diff).sum() / len(diff)) ** 0.5 * const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5
        else:
            return ((diff * diff).sum() / len(diff)) ** 0.5 * len(diff) ** 0.5

    def cal_information_ratio(self, volatility):
        strategy_rets = self.strategy_current_annualized_returns[-1]
        benchmark_rets = self.benchmark_current_annualized_returns[-1]

        if volatility == 0:
            return np.nan
        return (strategy_rets - benchmark_rets) / volatility

    def cal_alpha(self):
        beta = self._risk.beta

        strategy_rets = self.strategy_current_annualized_returns[-1]
        benchmark_rets = self.benchmark_current_annualized_returns[-1]

        alpha = strategy_rets - (self.riskfree_total_returns + beta * (benchmark_rets - self.riskfree_total_returns))
        return alpha

    def cal_beta(self):
        if len(self.strategy_current_daily_returns) <= 1:
            return 0.
        cov = np.cov(np.vstack([
            self.strategy_current_daily_returns,
            self.benchmark_current_daily_returns,
        ]), ddof=1)
        val = cov[1][1]
        if val == 0:
            return np.nan
        beta = cov[0][1] / val

        return beta

    def cal_sharpe(self):
        volatility = self._risk.volatility
        strategy_rets = self.strategy_current_annualized_returns[-1]

        if volatility != 0:
            sharpe = (strategy_rets - self.riskfree_total_returns) / volatility
        else:
            sharpe = np.nan

        return sharpe

    def cal_sortino(self):
        strategy_rets = self.strategy_current_annualized_returns[-1]
        downside_risk = self._risk.downside_risk

        if downside_risk != 0:
            sortino = (strategy_rets - self.riskfree_total_returns) / downside_risk
        else:
            sortino = np.nan
        return sortino

    def cal_downside_risk(self):
        mask = self.strategy_current_daily_returns < self.benchmark_current_daily_returns
        diff = self.strategy_current_daily_returns[mask] - self.benchmark_current_daily_returns[mask]
        if len(diff) <= 1:
            return 0.

        if self.is_annualized:
            return ((diff * diff).sum() / len(diff)) ** 0.5 * const.DAYS_CNT.TRADING_DAYS_A_YEAR ** 0.5
        else:
            return ((diff * diff).sum() / len(diff)) ** 0.5 * len(diff) ** 0.5

    def __repr__(self):
        return "RiskCal({0})".format(self.__dict__)

    def to_json(self):
        blacklist = ["trading_index"]
        data = {key: value for key, value in self.__dict__.items() if key not in blacklist}
        data["trading_index"] = self.trading_index.tolist()
        json_str = jsonpickle.encode(data)
        return json_str

    def from_json(self, json_str):
        data = jsonpickle.decode(json_str)
        data["trading_index"] = pd.Index(data["trading_index"])

        self.__dict__.update(data)

    def get_state(self):

        return self.to_json().encode('utf-8')

    def set_state(self, state):
        self.from_json(state.decode('utf-8'))




if __name__ == '__main__':
    import os
    import datetime
    from rqalpha.data import LocalDataProxy

    data_proxy = LocalDataProxy(os.path.expanduser("~/data/bundle"))
    trading_dates = data_proxy.get_trading_dates("2016-11-01", "2050-01-01")

    risk_cal = RiskCal(None)
    risk_cal.init_data(trading_dates)

    risk_cal.calculate(datetime.date(2016, 11, 1), 0.01, 0.01, 0.03)

    risk_cal2 = RiskCal(None)

    risk_cal2.from_json(risk_cal.to_json())
