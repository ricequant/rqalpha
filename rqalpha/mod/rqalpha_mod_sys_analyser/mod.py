# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import os
import pandas
import pickle
import jsonpickle
import datetime
from operator import attrgetter
from collections import defaultdict
from typing import Dict, Optional, List, Tuple, Union, Iterable

import numpy as np
import pandas as pd
from rqrisk import Risk, WEEKLY

from rqalpha.const import EXIT_CODE, DEFAULT_ACCOUNT_TYPE, INSTRUMENT_TYPE, POSITION_DIRECTION
from rqalpha.core.events import EVENT
from rqalpha.interface import AbstractMod, AbstractPosition
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils import INST_TYPE_IN_STOCK_ACCOUNT
from rqalpha.utils.logger import user_system_log
from rqalpha.const import DAYS_CNT
from rqalpha.api import export_as_api
from .plot.utils import max_ddd as _max_ddd
from .plot_store import PlotStore


def _get_yearly_risk_free_rates(
        data_proxy, start_date: datetime.date, end_date: datetime.date
) -> Iterable[Tuple[int, float]]:
    while start_date <= end_date:
        year = start_date.year
        yield year, data_proxy.get_risk_free_rate(start_date, min(end_date, datetime.date(year, 12, 31)))
        start_date = datetime.date(year + 1, 1, 1)


class AnalyserMod(AbstractMod):
    def __init__(self):
        self._env = None
        self._mod_config = None
        self._enabled = False

        self._orders = []
        self._trades = []
        self._total_portfolios = []
        self._total_benchmark_portfolios = []
        self._sub_accounts = defaultdict(list)
        self._positions = defaultdict(list)

        self._benchmark_daily_returns = []
        self._portfolio_daily_returns = []

        self._benchmark: Optional[List[Tuple[str, float]]] = None

        self._plot_store = None

    def get_state(self):
        return jsonpickle.dumps({
            'benchmark_daily_returns': [float(v) for v in self._benchmark_daily_returns],
            'portfolio_daily_returns': [float(v) for v in self._portfolio_daily_returns],
            'total_portfolios': self._total_portfolios,
            'total_benchmark_portfolios': self._total_benchmark_portfolios,
            'sub_accounts': self._sub_accounts,
            'positions': self._positions,
            'orders': self._orders,
            'trades': self._trades,
        }).encode('utf-8')

    def set_state(self, state):
        value = jsonpickle.loads(state.decode('utf-8'))
        self._benchmark_daily_returns = value['benchmark_daily_returns']
        self._portfolio_daily_returns = value["portfolio_daily_returns"]
        self._total_portfolios = value['total_portfolios']
        self._total_benchmark_portfolios = value["total_benchmark_portfolios"]
        self._sub_accounts = value['sub_accounts']
        self._positions = value["positions"]
        self._orders = value['orders']
        self._trades = value["trades"]

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config
        self._enabled = (
            mod_config.record or mod_config.plot or mod_config.output_file or
            mod_config.plot_save_file or mod_config.report_save_path or mod_config.bechmark
        )
        if self._enabled:
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._subscribe_events)

            if not mod_config.benchmark:
                if getattr(env.config.base, "benchmark", None):
                    user_system_log.warning(
                        _("config 'base.benchmark' is deprecated, use 'mod.sys_analyser.benchmark' instead")
                    )
                    mod_config.benchmark = getattr(env.config.base, "benchmark")
            if mod_config.benchmark:
                self._benchmark = self._parse_benchmark(mod_config.benchmark)

            self._plot_store = PlotStore(env)
            export_as_api(self._plot_store.plot)

    def get_benchmark_daily_returns(self):
        if self._benchmark is None:
            return np.nan
        daily_return_list = []
        weights = 0
        for benchmark in self._benchmark:
            bar = self._env.data_proxy.get_bar(benchmark[0], self._env.calendar_dt, '1d')
            if bar.close != bar.close:
                daily_return_list.append((0.0, benchmark[1]))
            else:
                daily_return_list.append((bar.close / bar.prev_close - 1.0, benchmark[1]))
            weights += benchmark[1]
        return sum([daily[0] * daily[1] / weights for daily in daily_return_list])

    def _subscribe_events(self, _):
        self._env.event_bus.add_listener(EVENT.TRADE, self._collect_trade)
        self._env.event_bus.add_listener(EVENT.ORDER_CREATION_PASS, self._collect_order)
        self._env.event_bus.add_listener(EVENT.POST_SETTLEMENT, self._collect_daily)

    def _collect_trade(self, event):
        self._trades.append(self._to_trade_record(event.trade))

    def _collect_order(self, event):
        self._orders.append(event.order)

    def _collect_daily(self, _):
        date = self._env.calendar_dt.date()
        portfolio = self._env.portfolio

        self._portfolio_daily_returns.append(portfolio.daily_returns)
        self._total_portfolios.append(self._to_portfolio_record(date, portfolio))
        self._benchmark_daily_returns.append(self.get_benchmark_daily_returns())
        self._total_benchmark_portfolios.append({
            "date": date,
            "unit_net_value": (np.array(self._benchmark_daily_returns) + 1).prod()
        })

        for account_type, account in self._env.portfolio.accounts.items():
            self._sub_accounts[account_type].append(self._to_account_record(date, account))
            pos_dict = {}
            for pos in account.get_positions():
                pos_dict.setdefault(pos.order_book_id, {})[pos.direction] = pos

            for order_book_id, pos in pos_dict.items():
                self._positions[account_type].append(self._to_position_record(
                    date, order_book_id, pos.get(POSITION_DIRECTION.LONG), pos.get(POSITION_DIRECTION.SHORT)
                ))

    def _symbol(self, order_book_id):
        return self._env.data_proxy.instrument(order_book_id).symbol

    @staticmethod
    def _parse_benchmark(benchmarks):
        # type: (Union[str, Dict]) -> List[Tuple[str, float]]
        # --benchmark 000001.XSHE:1000,IF1701:-1
        result = []
        if not isinstance(benchmarks, str):
            # 字典
            for order_book_id, weight in benchmarks.items():
                result.append((order_book_id, float(weight)))
            return result
        benchmark_list = benchmarks.split(',')
        if len(benchmark_list) == 1:
            if len(benchmark_list[0].split(':')) > 1:
                result.append((benchmark_list[0].split(':')[0], 1.0))
                return result
            result.append((benchmark_list[0], 1.0))
            return result
        for s in benchmark_list:
            try:
                order_book_id, weight = s.split(':')
            except ValueError:
                raise RuntimeError(
                    _(u"invalid init benchmark {}, should be in format 'order_book_id:weight'").format(s))

            try:
                result.append((order_book_id, float(weight)))
            except ValueError:
                raise RuntimeError(_(u"invalid weight for instrument {order_book_id}: {weight}").format(
                    order_book_id=order_book_id, weight=weight))
        return result

    @staticmethod
    def _safe_convert(value, ndigits=4):
        try:
            return round(float(value), ndigits)
        except TypeError:
            return value

    def _to_portfolio_record(self, date, portfolio):
        return {
            'date': date,
            'cash': self._safe_convert(portfolio.cash),
            'total_value': self._safe_convert(portfolio.total_value),
            'market_value': self._safe_convert(portfolio.market_value),
            'unit_net_value': self._safe_convert(portfolio.unit_net_value, 6),
            'units': portfolio.units,
            'static_unit_net_value': self._safe_convert(portfolio.static_unit_net_value),
        }

    ACCOUNT_FIELDS_MAP = {
        DEFAULT_ACCOUNT_TYPE.STOCK: [],
        DEFAULT_ACCOUNT_TYPE.FUTURE: ['position_pnl', 'trading_pnl', 'daily_pnl', 'margin'],
        DEFAULT_ACCOUNT_TYPE.BOND: [],
    }

    def _to_account_record(self, date, account):
        data = {
            'date': date,
            'cash': self._safe_convert(account.cash),
            'transaction_cost': self._safe_convert(account.transaction_cost),
            'market_value': self._safe_convert(account.market_value),
            'total_value': self._safe_convert(account.total_value),
        }

        for f in self.ACCOUNT_FIELDS_MAP[account.type]:
            data[f] = self._safe_convert(getattr(account, f))

        return data

    LONG_ONLY_INS_TYPE = INST_TYPE_IN_STOCK_ACCOUNT + [INSTRUMENT_TYPE.CONVERTIBLE, INSTRUMENT_TYPE.BOND]

    def _to_position_record(self, date, order_book_id, long, short):
        # type: (datetime.date, str, AbstractPosition, AbstractPosition) -> Dict
        instrument = self._env.data_proxy.instrument(order_book_id)
        data = {
            'order_book_id': order_book_id,
            'symbol': self._symbol(order_book_id),
            'date': date,
        }
        if instrument.type in self.LONG_ONLY_INS_TYPE + [INSTRUMENT_TYPE.REPO]:
            for field in ['quantity', 'last_price', 'avg_price', 'market_value']:
                data[field] = self._safe_convert(getattr(long, field, None))
        else:
            position = long or short
            if position:
                for field in ['margin', 'contract_multiplier', 'last_price']:
                    data[field] = self._safe_convert(getattr(position, field))
            direction_pos_iter = ((pos.direction, pos) for pos in (long, short) if pos)
            for direction_prefix, pos in direction_pos_iter:
                data[direction_prefix + "_pnl"] = self._safe_convert(getattr(pos, "pnl", None))
                data[direction_prefix + "_margin"] = self._safe_convert(pos.margin)
                data[direction_prefix + "_quantity"] = self._safe_convert(pos.quantity)
                data[direction_prefix + "_avg_open_price"] = self._safe_convert(getattr(pos, "avg_price", None))
        return data

    def _to_trade_record(self, trade):
        return {
            'datetime': trade.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'trading_datetime': trade.trading_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'order_book_id': trade.order_book_id,
            'symbol': self._symbol(trade.order_book_id),
            'side': trade.side.name,
            'position_effect': trade.position_effect.name,
            'exec_id': trade.exec_id,
            'tax': trade.tax,
            'commission': trade.commission,
            'last_quantity': trade.last_quantity,
            'last_price': self._safe_convert(trade.last_price),
            'order_id': trade.order_id,
            'transaction_cost': trade.transaction_cost,
        }

    def tear_down(self, code, exception=None):
        if code != EXIT_CODE.EXIT_SUCCESS or not self._enabled:
            return

        # 当 PRE_SETTLEMENT 事件没有被触发当时候，self._total_portfolio 为空list
        if len(self._total_portfolios) == 0:
            return

        strategy_name = os.path.basename(self._env.config.base.strategy_file).split(".")[0]
        data_proxy = self._env.data_proxy
        start_date, end_date = attrgetter("start_date", "end_date")(self._env.config.base)
        summary = {
            'strategy_name': strategy_name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'strategy_file': self._env.config.base.strategy_file,
            'run_type': self._env.config.base.run_type.value,
            "starting_cash": ",".join(f"{t}:{c}" for t, c in self._env.config.base.accounts.items())
        }
        for account_type, starting_cash in self._env.config.base.accounts.items():
            summary[account_type] = starting_cash
        if self._benchmark:
            if len(self._benchmark) == 1:
                benchmark_obid, _ = self._benchmark[0]
                summary["benchmark"] = benchmark_obid
                summary["benchmark_symbol"] = self._env.data_proxy.instrument(benchmark_obid).symbol
            else:
                summary["benchmark"] = ",".join(f"{o}:{w}" for o, w in self._benchmark)

        risk_free_rate = data_proxy.get_risk_free_rate(self._env.config.base.start_date, self._env.config.base.end_date)
        risk = Risk(
            np.array(self._portfolio_daily_returns), np.array(self._benchmark_daily_returns), risk_free_rate
        )
        summary.update({
            'alpha': risk.alpha,
            'beta': risk.beta,
            'sharpe': risk.sharpe,
            'excess_sharpe': risk.excess_sharpe,
            'information_ratio': risk.information_ratio,
            'downside_risk': risk.annual_downside_risk,
            'tracking_error': risk.annual_tracking_error,
            'sortino': risk.sortino,
            'volatility': risk.annual_volatility,
            'excess_volatility': risk.excess_volatility,
            'excess_annual_volatility': risk.excess_annual_volatility,
            'max_drawdown': risk.max_drawdown,
            'excess_max_drawdown': risk.excess_max_drawdown,
            'excess_returns': risk.excess_return_rate,
            'excess_annual_returns': risk.excess_annual_return,
            'var': risk.var,
        })

        summary.update({
            'total_value': self._env.portfolio.total_value,
            'cash': self._env.portfolio.cash,
            'total_returns': self._env.portfolio.total_returns,
            'annualized_returns': self._env.portfolio.annualized_returns,
            'unit_net_value': self._env.portfolio.unit_net_value,
            'units': self._env.portfolio.units,
        })

        if self._benchmark:
            benchmark_total_returns = (np.array(self._benchmark_daily_returns) + 1.0).prod() - 1.0
            summary['benchmark_total_returns'] = benchmark_total_returns
            date_count = len(self._benchmark_daily_returns)
            benchmark_annualized_returns = (benchmark_total_returns + 1) ** (DAYS_CNT.TRADING_DAYS_A_YEAR / date_count) - 1
            summary['benchmark_annualized_returns'] = benchmark_annualized_returns

            # 新增一个超额累计收益
            summary['excess_cum_returns'] = summary["total_returns"] - summary["benchmark_total_returns"]

        trades = pd.DataFrame(self._trades)
        if 'datetime' in trades.columns:
            trades = trades.set_index(pd.DatetimeIndex(trades['datetime']))

        df = pd.DataFrame(self._total_portfolios)
        df['date'] = pd.to_datetime(df['date'])
        total_portfolios = df.set_index('date').sort_index()
        weekly_nav = df.resample("W", on="date").last().set_index("date").unit_net_value.dropna()
        weekly_returns = (weekly_nav / weekly_nav.shift(1).fillna(1)).fillna(0) - 1

        # 最长回撤持续期
        max_ddd = _max_ddd(total_portfolios.unit_net_value.values, total_portfolios.index)
        summary["max_drawdown_duration"] = max_ddd
        summary.update({
            "max_drawdown_duration_start_date": str(max_ddd.start_date),
            "max_drawdown_duration_end_date": str(max_ddd.end_date),
            "max_drawdown_duration_days": (max_ddd.end_date - max_ddd.start_date).days,
        })

        result_dict = {
            'summary': summary,
            'trades': trades,
            'portfolio': total_portfolios,
        }

        if not trades.empty and all(
                trades.order_book_id.str.endswith(".XSHE") | trades.order_book_id.str.endswith(".XSHG")
        ):
            # 策略仅交易股票、指数、场内基金等品种时才计算换手率
            trades_values = trades.last_price * trades.last_quantity
            market_values = total_portfolios.market_value
            summary["turnover"] = trades_values.sum() / market_values.mean() / 2
            avg_daily_turnover = (trades_values.groupby(trades.index.date).sum() / market_values / 2)
            with pd.option_context('mode.use_inf_as_na', True):
                summary["avg_daily_turnover"] = avg_daily_turnover.fillna(0).mean()
        else:
            summary["turnover"] = np.nan

        if self._benchmark:
            df = pd.DataFrame(self._total_benchmark_portfolios)
            df['date'] = pd.to_datetime(df['date'])
            benchmark_portfolios = df.set_index('date').sort_index()
            weekly_b_nav = df.resample("W", on="date").last().set_index("date").unit_net_value.dropna()
            weekly_b_returns = (weekly_b_nav / weekly_b_nav.shift(1).fillna(1)).fillna(0) - 1
            result_dict['benchmark_portfolio'] = benchmark_portfolios
            # 超额收益最长回撤持续期
            ex_returns = total_portfolios.unit_net_value - benchmark_portfolios.unit_net_value
            max_ddd = _max_ddd(ex_returns + 1, total_portfolios.index)
            result_dict["summary"]["excess_max_drawdown_duration"] = max_ddd
            result_dict["summary"]["excess_max_drawdown_duration_start_date"] = str(max_ddd.start_date)
            result_dict["summary"]["excess_max_drawdown_duration_end_date"] = str(max_ddd.end_date)
            result_dict["summary"]["excess_max_drawdown_duration_days"] = (max_ddd.end_date - max_ddd.start_date).days
        else:
            weekly_b_returns = pandas.Series(index=weekly_returns.index)
        weekly_risk = Risk(weekly_returns, weekly_b_returns, risk_free_rate, WEEKLY)
        summary.update({
            "weekly_alpha": weekly_risk.alpha,
            "weekly_beta": weekly_risk.beta,
            "weekly_sharpe": weekly_risk.sharpe,
            "weekly_sortino": weekly_risk.sortino,
            'weekly_information_ratio': weekly_risk.information_ratio,
            "weekly_tracking_error": weekly_risk.tracking_error,
            "weekly_max_drawdown": weekly_risk.max_drawdown,
        })

        plots = self._plot_store.get_plots()
        if plots:
            plots_items = defaultdict(dict)
            for series_name, value_dict in plots.items():
                for date, value in value_dict.items():
                    plots_items[date][series_name] = value
                    plots_items[date]["date"] = date

            df = pd.DataFrame([dict_data for date, dict_data in plots_items.items()])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            result_dict["plots"] = df

        for account_type, account in self._env.portfolio.accounts.items():
            account_name = account_type.lower()
            portfolios_list = self._sub_accounts[account_type]
            df = pd.DataFrame(portfolios_list)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            result_dict["{}_account".format(account_name)] = df

            positions_list = self._positions[account_type]
            df = pd.DataFrame(positions_list)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()
            result_dict["{}_positions".format(account_name)] = df

        result_dict["yearly_risk_free_rates"] = dict(_get_yearly_risk_free_rates(data_proxy, start_date, end_date))

        if self._mod_config.output_file:
            with open(self._mod_config.output_file, 'wb') as f:
                pickle.dump(result_dict, f)

        if self._mod_config.report_save_path:
            from .report import generate_report
            generate_report(result_dict, self._mod_config.report_save_path)

        if self._mod_config.plot or self._mod_config.plot_save_file:
            from .plot import plot_result
            plot_config = self._mod_config.plot_config
            plot_result(
                result_dict, self._mod_config.plot, self._mod_config.plot_save_file,
                plot_config.weekly_indicators, plot_config.open_close_points
            )

        return result_dict
