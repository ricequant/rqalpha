# -*- coding: utf-8 -*-
import os
import pickle
from collections import OrderedDict, defaultdict

import six
from enum import Enum
import numpy as np
import pandas as pd

from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT
from rqalpha.const import ACCOUNT_TYPE, EXIT_CODE
from rqalpha.utils.risk import Risk
from rqalpha.utils.repr import properties
from rqalpha.execution_context import ExecutionContext


class AnalyserMod(AbstractMod):
    def __init__(self):
        self._env = None
        self._mod_config = None
        self._enabled = False
        self._result = None

        self._orders = defaultdict(list)
        self._trades = defaultdict(list)
        self._portfolios = OrderedDict()
        self._portfolios_dict = defaultdict(OrderedDict)

        self._benchmark_daily_returns = []
        self._portfolio_daily_returns = []

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config
        self._enabled = (self._mod_config.plot or self._mod_config.output_file or
                         self._mod_config.plot_save_file or self._mod_config.report_save_path)

        if self._enabled:
            env.event_bus.add_listener(EVENT.POST_SETTLEMENT, self._collect_daily)
            env.event_bus.add_listener(EVENT.TRADE, self._collect_trade)
            env.event_bus.add_listener(EVENT.ORDER_CREATION_PASS, self._collect_order)

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
        self._benchmark_daily_returns.append(benchmark_daily_returns)
        self._portfolio_daily_returns.append(portfolio.daily_returns)

        self._portfolios[date] = portfolio

        # 单独分账号保存自己的
        for account_type, account in six.iteritems(self._env.accounts):
            self._portfolios_dict[account_type][date] = account.get_portfolio(date)

    def _symbol(self, order_book_id):
        return self._env.data_proxy.instruments(order_book_id).symbol

    @staticmethod
    def _safe_convert(value, ndigits=3):
        if isinstance(value, Enum):
            return value.name

        if isinstance(value, (float, np.float64, np.float32, np.float16, np.float128)):
            return round(value, ndigits)

        return value

    def _to_portfolio_record(self, date, portfolio):
        data = {
            k: self._safe_convert(v, 3) for k, v in six.iteritems(properties(portfolio))
            if not k.startswith('_') and not k.endswith('_') and k not in {
                "positions", "start_date", "starting_cash"
            }
        }
        data['date'] = date
        return data

    def _to_portfolio_record2(self, date, portfolio):
        data = {
            k: self._safe_convert(v, 3) for k, v in six.iteritems(portfolio.__dict__)
            if not k.startswith('_') and not k.endswith('_') and k not in {
                "positions", "start_date", "starting_cash"
            }
            }
        data['date'] = date
        return data

    def _to_position_record(self, date, order_book_id, position):
        data = {
            k: self._safe_convert(v, 3) for k, v in six.iteritems(properties(position))
            if not k.startswith('_') and not k.endswith('_')
            }
        data['order_book_id'] = order_book_id
        data['symbol'] = self._symbol(order_book_id)
        data['date'] = date

    def _to_trade_record(self, trade):
        data = {
            k: self._safe_convert(v) for k, v in six.iteritems(properties(trade))
            if not k.startswith('_') and not k.endswith('_') and k != 'order'
        }
        data['order_book_id'] = trade.order.order_book_id
        data['symbol'] = self._symbol(trade.order.order_book_id)
        data['datetime'] = data['datetime'].strftime("%Y-%m-%d %H:%M:%S")
        data['trading_datetime'] = data['trading_datetime'].strftime("%Y-%m-%d %H:%M:%S")
        return data

    def tear_down(self, code, exception=None):
        if code != EXIT_CODE.EXIT_SUCCESS or not self._enabled:
            return

        strategy_name = os.path.basename(self._env.config.base.strategy_file).split(".")[0]
        data_proxy = self._env.data_proxy

        summary = {
            'strategy_name': strategy_name,
        }
        for k, v in six.iteritems(self._env.config.base.__dict__):
            if k in ["trading_calendar", "account_list", "timezone", "persist_mode",
                     "resume_mode", "data_bundle_path", "handle_split", "persist"]:
                continue
            summary[k] = self._safe_convert(v, 2)

        risk = Risk(np.array(self._portfolio_daily_returns), np.array(self._benchmark_daily_returns),
                    data_proxy.get_risk_free_rate(self._env.config.base.start_date, self._env.config.base.end_date),
                    (self._env.config.base.end_date - self._env.config.base.start_date).days + 1)
        summary.update({
            'alpha': self._safe_convert(risk.alpha, 3),
            'beta': self._safe_convert(risk.beta, 3),
            'sharpe': self._safe_convert(risk.sharpe, 3),
            'information_ratio': self._safe_convert(risk.information_ratio, 3),
            'downside_risk': self._safe_convert(risk.annual_downside_risk, 3),
            'tracking_error': self._safe_convert(risk.annual_tracking_error, 3),
            'sortino': self._safe_convert(risk.sortino, 3),
            'volatility': self._safe_convert(risk.annual_volatility, 3),
            'max_drawdown': self._safe_convert(risk.max_drawdown, 3),
        })

        latest_portfolio = list(self._portfolios.values())[-1]
        summary.update({
            k: self._safe_convert(v, 3) for k, v in six.iteritems(properties(latest_portfolio))
            if k not in ["positions", "daily_returns", "daily_pnl"]
        })

        if ACCOUNT_TYPE.BENCHMARK in self._portfolios_dict:
            latest_benchmark_portfolio = list(self._portfolios_dict[ACCOUNT_TYPE.BENCHMARK].values())[-1]
            summary['benchmark_total_returns'] = latest_benchmark_portfolio.total_returns
            summary['benchmark_annualized_returns'] = latest_benchmark_portfolio.annualized_returns

        total_portfolio_list = []
        for date, portfolio in six.iteritems(self._portfolios):
            total_portfolio_list.append(self._to_portfolio_record(date, portfolio))

        positions_list_dict = defaultdict(list)
        portfolios_list_dict = defaultdict(list)
        for account_type, portfolio_order_dict in six.iteritems(self._portfolios_dict):
            positions_list = positions_list_dict[account_type]
            portfolios_list = portfolios_list_dict[account_type]

            for date, portfolio in six.iteritems(portfolio_order_dict):
                portfolios_list.append(self._to_portfolio_record2(date, portfolio))

                for order_book_id, position in six.iteritems(portfolio.positions):
                    positions_list.append(self._to_position_record(date, order_book_id, position))

        trades_list = []
        for date in six.iterkeys(self._portfolios):
            for trade in self._trades[date]:
                trades_list.append(self._to_trade_record(trade))
        trades = pd.DataFrame(trades_list)
        if 'datetime' in trades.columns:
            trades = trades.set_index('datetime')

        df = pd.DataFrame(total_portfolio_list)
        df['date'] = pd.to_datetime(df['date'])
        total_portfolios = df.set_index('date').sort_index()

        result_dict = {
            'summary': summary,
            'trades': trades,
            'total_portfolios': total_portfolios,
        }

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

        for account_type, account in six.iteritems(self._env.accounts):
            account_name = account_type.name.lower()
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

        self._result = result_dict

        if self._mod_config.output_file:
            with open(self._mod_config.output_file, 'wb') as f:
                pickle.dump(result_dict, f)

        if self._mod_config.plot:
            from rqalpha.plot import plot_result
            plot_result(result_dict)

        if self._mod_config.plot_save_file:
            from rqalpha.plot import plot_result
            plot_result(result_dict, False, self._mod_config.plot_save_file)

        if self._mod_config.report_save_path:
            from rqalpha.utils.report import generate_report
            generate_report(result_dict, self._mod_config.report_save_path)
