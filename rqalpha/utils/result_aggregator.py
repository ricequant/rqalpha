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

import six
import pandas as pd
from collections import OrderedDict, defaultdict

from ..events import Events
from ..const import ACCOUNT_TYPE
from ..utils.repr import properties
from ..utils import safe_round
from ..execution_context import ExecutionContext


class ResultAggregator(object):
    def __init__(self, env, risk_cal):
        env.event_bus.add_listener(Events.POST_SETTLEMENT, self._collect_daily)
        env.event_bus.add_listener(Events.TRADE, self._collect_trade)
        env.event_bus.add_listener(Events.ORDER_CREATION_PASS, self._collect_order)
        self._env = env
        self._orders = defaultdict(list)
        self._trades = defaultdict(list)

        self._portfolios = OrderedDict()
        self._portfolios_dict = defaultdict(OrderedDict)

        self._risk_free_rate = env.data_proxy.get_risk_free_rate(env.config.base.start_date,
                                                                 env.config.base.end_date)
        self._risk_cal = risk_cal

    def _collect_trade(self, account, trade):
        self._trades[trade.trading_datetime.date()].append(trade)

    def _collect_order(self, account, order):
        self._orders[order.trading_datetime.date()].append(order)

    def _collect_daily(self):
        try:
            benchmark_daily_returns = self._env.accounts[ACCOUNT_TYPE.BENCHMARK].portfolio.daily_returns
        except KeyError:
            benchmark_daily_returns = 0

        date = self._env.calendar_dt.date()
        portfolio = self._env.account.get_portfolio(date)
        self._portfolios[date] = portfolio

        self._risk_cal.calculate(date, portfolio.daily_returns, benchmark_daily_returns, self._risk_free_rate)

        # FIXME 千万不要删！会有严重后果！ET：我的锅
        tmp = self._risk_cal.risk

        # 单独分账号保存自己的
        for account_type, account in six.iteritems(self._env.accounts):
            self._portfolios_dict[account_type][date] = account.get_portfolio(date)

    def get_result_dict(self, strategy_name):
        """
        {
            summary[] - dict
            trades[] - dataframe
            positions[] - dataframe
            portfolios[] - dataframe
        }
        <— result_dict
        """
        from enum import Enum

        data_proxy = self._env.data_proxy

        def safe_convert(value, ndigits=3):
            value = safe_round(value, ndigits)
            if isinstance(value, Enum):
                value = str(value).split(".")[1]

            return value

        def symbol(order_book_id):
            return data_proxy.instruments(order_book_id).symbol

        def filter_keys(keys, blacklist=[]):
            return not key.startswith("_") and not key.endswith("_") and key not in blacklist

        # summary
        date, latest_portfolio = list((key, value) for key, value in six.iteritems(self._portfolios))[-1]
        risk = self._risk_cal.daily_risks[date]
        risk_keys = [
            "volatility", "max_drawdown",
            "alpha", "beta", "sharpe",
            "information_ratio", "downside_risk",
            "tracking_error", "sortino",
        ]

        summary = {
            "strategy_name": strategy_name,
        }
        for key, value in six.iteritems(self._env.config.base.__dict__):
            if key not in ["trading_calendar", "account_list", "timezone", "persist_mode",
                           "resume_mode", "data_bundle_path", "handle_split", "persist", "cal_risk_grid"]:
                summary[key] = safe_convert(value, 2)
        for key in risk_keys:
            summary[key] = safe_convert(getattr(risk, key), 3)
        for key, value in six.iteritems(properties(latest_portfolio)):
            if key not in ["positions", "daily_returns", "daily_pnl"]:
                summary[key] = safe_convert(value, 3)
        # summary["start_date"] = summary["start_date"].strftime("%Y-%m-%d")
        # summary["end_date"] = summary["end_date"].strftime("%Y-%m-%d")

        # add benchmark
        if ACCOUNT_TYPE.BENCHMARK in self._portfolios_dict:
            _, latest_benchmark_portfolio = list((key, value) for key, value in six.iteritems(self._portfolios_dict[ACCOUNT_TYPE.BENCHMARK]))[-1]
            for key in ["total_returns", "annualized_returns"]:
                summary["benchmark_{}".format(key)] = getattr(latest_benchmark_portfolio, key)

        trades_list = []
        total_portfolios_list = []
        positions_list_dict = defaultdict(list)
        portfolios_list_dict = defaultdict(list)
        portfolio_blacklist = ["positions", "start_date", "starting_cash"]

        # total portfolios
        for date, portfolio in six.iteritems(self._portfolios):
            # portfolio
            # dict_data = {"date": date.strftime("%Y-%m-%d")}
            dict_data = {"date": date}
            for key, value in six.iteritems(properties(portfolio)):
                if filter_keys(key, portfolio_blacklist):
                    dict_data[key] = safe_convert(value, 3)
            total_portfolios_list.append(dict_data)

        # stock/future portfolio
        for account_type, portfolio_order_dict in six.iteritems(self._portfolios_dict):
            positions_list = positions_list_dict[account_type]
            portfolios_list = portfolios_list_dict[account_type]

            for date, portfolio in six.iteritems(portfolio_order_dict):
                # portfolio
                # dict_data = {"date": date.strftime("%Y-%m-%d")}
                dict_data = {"date": date}
                for key, value in six.iteritems(portfolio.__dict__):
                    if filter_keys(key, portfolio_blacklist):
                        dict_data[key] = safe_convert(value, 3)
                portfolios_list.append(dict_data)

                # positions
                for order_book_id, position in six.iteritems(portfolio.positions):
                    dict_data = {
                        # "date": date.strftime("%Y-%m-%d"),
                        "date": date,
                    }
                    for key, value in six.iteritems(position.__dict__):
                        if filter_keys(key):
                            dict_data[key] = safe_convert(value, 3)
                    dict_data["order_book_id"] = order_book_id
                    dict_data["symbol"] = symbol(order_book_id)
                    positions_list.append(dict_data)

        # trades
        for date, _ in six.iteritems(self._portfolios):
            for trade in self._trades[date]:
                dict_data = {
                    "side": safe_convert(trade.order.side),
                }
                for key, value in six.iteritems(properties(trade)):
                    if filter_keys(key, ["order"]):
                        dict_data[key] = safe_convert(value, 3)
                dict_data["order_book_id"] = trade.order.order_book_id
                dict_data["symbol"] = symbol(trade.order.order_book_id)
                dict_data["datetime"] = dict_data["datetime"].strftime("%Y-%m-%d %H:%M:%S")
                dict_data["trading_datetime"] = dict_data["trading_datetime"].strftime("%Y-%m-%d %H:%M:%S")
                trades_list.append(dict_data)

        # fix dataframe
        trades = pd.DataFrame(trades_list)
        if "datetime" in trades.columns:
            trades = trades.set_index("datetime")

        df = pd.DataFrame(total_portfolios_list)
        df["date"] = pd.to_datetime(df["date"])
        total_portfolios = df.set_index("date").sort_index()

        result_dict = {
            "summary": summary,
            "trades": trades,
            "total_portfolios": total_portfolios,
        }

        # plots
        if ExecutionContext.plots is not None:
            plots = ExecutionContext.plots.get_plots()
            plots_items = defaultdict(dict)
            for series_name, value_dict in six.iteritems(plots):
                for date, value in six.iteritems(value_dict):
                    plots_items[date][series_name] = value
                    plots_items[date]["date"] = date

            df = pd.DataFrame([dict_data for date, dict_data in six.iteritems(plots_items)])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            result_dict["plots"] = df

        # extra
        for account_type, account in six.iteritems(self._env.accounts):
            account_name = str(account_type).split(".")[1].lower()
            portfolios_list = portfolios_list_dict[account_type]
            df = pd.DataFrame(portfolios_list)
            df["date"] = pd.to_datetime(df["date"])
            portfolios_df = df.set_index("date").sort_index()
            result_dict["{}_portfolios".format(account_name)] = portfolios_df

            positions_list = positions_list_dict[account_type]
            positions_df = pd.DataFrame(positions_list)
            if "date" in positions_df.columns:
                positions_df["date"] = pd.to_datetime(positions_df["date"])
                positions_df = positions_df.set_index("date").sort_index()
            result_dict["{}_positions".format(account_name)] = positions_df

        return result_dict

    def get_result(self):
        risk_cal = self._risk_cal
        columns = [
            "daily_returns",
            "total_returns",
            "annualized_returns",
            "market_value",
            "portfolio_value",
            # "total_commission",
            # "total_tax",
            "daily_pnl",
            "positions",
            "cash",
        ]
        risk_keys = [
            "volatility", "max_drawdown",
            "alpha", "beta", "sharpe",
            "information_ratio", "downside_risk",
            "tracking_error", "sortino",
        ]

        data = []
        for date, portfolio in six.iteritems(self._portfolios):
            # print(date, portfolio)
            # portfolio
            items = {"date": pd.Timestamp(date)}
            for key in columns:
                items[key] = getattr(portfolio, key)

            items["trades"] = self._trades[date]

            # risk
            risk = risk_cal.daily_risks[date]
            for risk_key in risk_keys:
                items[risk_key] = getattr(risk, risk_key)

            idx = risk_cal.trading_index.get_loc(date)
            items["benchmark_total_returns"] = risk_cal.benchmark_total_returns[idx]
            items["benchmark_daily_returns"] = risk_cal.benchmark_total_daily_returns[idx]
            items["benchmark_annualized_returns"] = risk_cal.benchmark_annualized_returns[idx]

            data.append(items)

        results_df = pd.DataFrame(data)
        results_df.set_index("date", inplace=True)

        return results_df
