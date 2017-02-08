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

import os
import sys
from datetime import datetime
import pickle

import jsonpickle.ext.numpy as jsonpickle_numpy
import pytz
from six import iteritems

from .core.strategy import Strategy
from .api import helper as api_helper
from . import const
from .analyser.risk_cal import RiskCal
from .core.default_broker import DefaultBroker
from .core.default_event_source import DefaultEventSource
from .core.default_strategy_loader import FileStrategyLoader
from .core.strategy_universe import StrategyUniverse
from .data.base_data_source import BaseDataSource
from .data.data_proxy import DataProxy
from .environment import Environment
from .events import Events
from .execution_context import ExecutionContext
from .interface import Persistable
from .mod.mod_handler import ModHandler
from .model.bar import BarMap
from .trader.account import MixedAccount
from .trader.global_var import GlobalVars
from .trader.strategy_context import StrategyContext
from .utils import create_custom_exception, run_with_user_log_disabled
from .utils.exception import CustomException, is_user_exc, patch_user_exc
from .utils.i18n import gettext as _
from .utils.logger import user_log, system_log, user_print, user_detail_log
from .utils.persisit_helper import CoreObjectsPersistProxy, PersistHelper
from .utils.result_aggregator import ResultAggregator
from .utils.scheduler import Scheduler
from .utils import scheduler as mod_scheduler
from .plot import plot_result


jsonpickle_numpy.register_handlers()


def _adjust_start_date(config, data_proxy):
    origin_start_date, origin_end_date = config.base.start_date, config.base.end_date
    start, end = data_proxy.available_data_range(config.base.frequency)

    # print(repr(start), repr(end))
    config.base.start_date = max(start, config.base.start_date)
    config.base.end_date = min(end, config.base.end_date)
    config.base.trading_calendar = data_proxy.get_trading_dates(config.base.start_date, config.base.end_date)
    if len(config.base.trading_calendar) == 0:
        raise patch_user_exc(ValueError(_('There is no trading day between {start_date} and {end_date}.').format(
            start_date=origin_start_date, end_date=origin_end_date)))
    config.base.start_date = config.base.trading_calendar[0].date()
    config.base.end_date = config.base.trading_calendar[-1].date()
    config.base.timezone = pytz.utc


def _validate_benchmark(config, data_proxy):
    benchmark = config.base.benchmark
    if benchmark is None:
        return
    instrument = data_proxy.instruments(benchmark)
    if instrument.order_book_id == "000300.XSHG":
        # 000300.XSHG 数据进行了补齐，因此认为只要benchmark设置了000300.XSHG，就存在数据，不受限于上市日期。
        return
    if not instrument:
        raise patch_user_exc(ValueError(_('invalid benchmark {}').format(benchmark)))

    config = Environment.get_instance().config
    start_date = config.base.start_date
    end_date = config.base.end_date
    if instrument.listed_date.date() > start_date:
        raise patch_user_exc(ValueError(
            _("benchmark {benchmark} has not been listed on {start_date}").format(benchmark=benchmark,
                                                                                  start_date=start_date)))
    if instrument.de_listed_date.date() < end_date:
        raise patch_user_exc(ValueError(
            _("benchmark {benchmark} has been de_listed on {end_date}").format(benchmark=benchmark,
                                                                               end_date=end_date)))


def create_base_scope():
    import copy

    from . import user_module
    scope = copy.copy(user_module.__dict__)
    scope.update({
        "logger": user_log,
        "print": user_print,
    })

    return scope


def run(config):
    env = Environment(config)
    persist_helper = None
    init_succeed = False

    try:
        env.set_strategy_loader(FileStrategyLoader())
        env.set_global_vars(GlobalVars())
        mod_handler = ModHandler(env)
        mod_handler.start_up()

        if not env.data_source:
            env.set_data_source(BaseDataSource(config.base.data_bundle_path))

        env.set_data_proxy(DataProxy(env.data_source))
        ExecutionContext.data_proxy = env.data_proxy
        Scheduler.set_trading_dates_(env.data_source.get_trading_calendar())
        scheduler = Scheduler(config.base.frequency)
        mod_scheduler._scheduler = scheduler

        env._universe = StrategyUniverse()

        _adjust_start_date(env.config, env.data_proxy)

        _validate_benchmark(env.config, env.data_proxy)

        broker = DefaultBroker(env)
        env.accounts = accounts = broker.get_accounts()
        env.account = account = MixedAccount(accounts)

        ExecutionContext.broker = broker
        ExecutionContext.accounts = accounts
        ExecutionContext.account = account
        ExecutionContext.config = env.config

        event_source = env.event_source
        if event_source is None:
            event_source = DefaultEventSource(env.data_proxy, env.config.base.account_list)

        bar_dict = BarMap(env.data_proxy, config.base.frequency)
        ctx = ExecutionContext(const.EXECUTION_PHASE.GLOBAL, bar_dict)
        ctx._push()

        # FIXME
        start_dt = datetime.combine(config.base.start_date, datetime.min.time())
        env.calendar_dt = ExecutionContext.calendar_dt = start_dt
        env.trading_dt = ExecutionContext.trading_dt = start_dt

        env.event_bus.publish_event(Events.POST_SYSTEM_INIT)

        scope = create_base_scope()
        scope.update({
            "g": env.global_vars
        })

        apis = api_helper.get_apis(config.base.account_list)
        scope.update(apis)

        scope = env.strategy_loader.load(env.config.base.strategy_file, scope)

        if env.config.extra.enable_profiler:
            enable_profiler(env, scope)

        risk_cal = RiskCal()
        risk_cal.init(config.base.trading_calendar, is_annualized=True, save_daily_risk=True)
        result_aggregator = ResultAggregator(env, risk_cal)

        ucontext = StrategyContext()
        user_strategy = Strategy(env.event_bus, scope, ucontext)

        if not config.extra.force_run_init_when_pt_resume:
            with run_with_user_log_disabled(disabled=config.base.resume_mode):
                user_strategy.init()

        if config.extra.context_vars:
            for k, v in config.extra.context_vars.items():
                setattr(ucontext, k, v)

        if config.base.persist:
            persist_provider = env.persist_provider
            persist_helper = PersistHelper(persist_provider, env.event_bus, config.base.persist_mode)
            persist_helper.register('core', CoreObjectsPersistProxy(scheduler))
            persist_helper.register('user_context', ucontext)
            persist_helper.register('global_vars', env.global_vars)
            persist_helper.register('universe', env._universe)
            if isinstance(event_source, Persistable):
                persist_helper.register('event_source', event_source)
            for k, v in accounts.items():
                persist_helper.register('{}_account'.format(k.name.lower()), v)
            for name, module in env.mod_dict.items():
                if isinstance(module, Persistable):
                    persist_helper.register('mod_{}'.format(name), module)
            # broker will restore open orders from account
            persist_helper.register('broker', broker)

            persist_helper.restore()

        init_succeed = True

        # When force_run_init_when_pt_resume is active,
        # we should run `init` after restore persist data
        if config.extra.force_run_init_when_pt_resume:
            assert config.base.resume_mode == True
            with run_with_user_log_disabled():
                user_strategy.init()

        for calendar_dt, trading_dt, event in event_source.events(config.base.start_date,
                                                                  config.base.end_date,
                                                                  config.base.frequency):
            ExecutionContext.calendar_dt = calendar_dt
            ExecutionContext.trading_dt = trading_dt
            env.calendar_dt = calendar_dt
            env.trading_dt = trading_dt
            for account in accounts.values():
                account.portfolio._current_date = trading_dt.date()

            if event == Events.BEFORE_TRADING:
                env.event_bus.publish_event(Events.PRE_BEFORE_TRADING)
                broker.before_trading()
                for account in accounts.values():
                    account.before_trading()
                scheduler.next_day_(trading_dt)
                env.event_bus.publish_event(Events.BEFORE_TRADING)
                with ExecutionContext(const.EXECUTION_PHASE.BEFORE_TRADING):
                    scheduler.before_trading_(ucontext)
                env.event_bus.publish_event(Events.POST_BEFORE_TRADING)
            elif event == Events.BAR:
                bar_dict.update_dt(calendar_dt)
                broker.update(calendar_dt, trading_dt, bar_dict)
                for account in accounts.values():
                    account.on_bar(bar_dict)
                env.event_bus.publish_event(Events.PRE_BAR)
                env.event_bus.publish_event(Events.BAR, bar_dict)
                with ExecutionContext(const.EXECUTION_PHASE.SCHEDULED, bar_dict):
                    scheduler.next_bar_(ucontext, bar_dict)
                env.event_bus.publish_event(Events.POST_BAR)
            elif event == Events.TICK:
                env.event_bus.publish_event(Events.PRE_TICK)
                env.event_bus.publish_event(Events.TICK)
                env.event_bus.publish_event(Events.POST_TICK)
            elif event == Events.AFTER_TRADING:
                env.event_bus.publish_event(Events.PRE_AFTER_TRADING)
                broker.after_trading()
                for account in accounts.values():
                    account.after_trading()
                env.event_bus.publish_event(Events.AFTER_TRADING)
                env.event_bus.publish_event(Events.POST_AFTER_TRADING)
            elif event == Events.SETTLEMENT:
                env.event_bus.publish_event(Events.PRE_SETTLEMENT)
                for account in accounts.values():
                    account.settlement()
                env.event_bus.publish_event(Events.SETTLEMENT)
                env.event_bus.publish_event(Events.POST_SETTLEMENT)
            else:
                raise RuntimeError('unknown event from event source: {}'.format(event))

        strategy_name = os.path.basename(env.config.base.strategy_file).split(".")[0]
        result_dict = result_aggregator.get_result_dict(strategy_name)

        output_generated_results(env, result_dict)

        mod_handler.tear_down(const.EXIT_CODE.EXIT_SUCCESS)
        system_log.debug("strategy run successfully, normal exit")
        return result_dict
    except CustomException as e:
        if init_succeed and env.config.base.persist and persist_helper:
            persist_helper.persist()

        user_detail_log.exception("strategy execute exception")
        user_log.error(e.error)
        mod_handler.tear_down(const.EXIT_CODE.EXIT_USER_ERROR, e)
    except Exception as e:
        if init_succeed and env.config.base.persist and persist_helper:
            persist_helper.persist()

        exc_type, exc_val, exc_tb = sys.exc_info()
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, config.base.strategy_file)

        user_log.error(user_exc.error)
        code = const.EXIT_CODE.EXIT_USER_ERROR
        if not is_user_exc(exc_val):
            system_log.exception("strategy execute exception")
            code = const.EXIT_CODE.EXIT_INTERNAL_ERROR
        else:
            user_detail_log.exception("strategy execute exception")

        mod_handler.tear_down(code, user_exc)


def enable_profiler(env, scope):
    # decorate line profiler
    import line_profiler
    import inspect
    env.profile_deco = profile_deco = line_profiler.LineProfiler()
    for name in scope:
        obj = scope[name]
        if getattr(obj, "__module__", None) != "rqalpha.user_module":
            continue
        if inspect.isfunction(obj):
            scope[name] = profile_deco(obj)
        if inspect.isclass(obj):
            for key, val in obj.__dict__.items():
                if inspect.isfunction(val):
                    setattr(obj, key, profile_deco(val))


def output_generated_results(env, result_dict):
    # output pickle file
    if env.config.extra.output_file is not None:
        pickle.dump(result_dict, open(env.config.extra.output_file, "wb"))

    # plot
    if env.config.extra.plot:
        plot_result(result_dict, show_windows=env.config.extra.plot)

    # save plot as image file
    if env.config.extra.plot_save_file:
        plot_result(result_dict, show_windows=False,
                    savefile=env.config.extra.plot_save_file)

    # generate report
    if env.config.extra.report_save_path:
        generate_report(result_dict, env.config.extra.report_save_path)

    # output line profiler result
    if env.profile_deco:  # config.extra.enable_profiler:
        from six import StringIO
        # profile_deco.dump_stats("{}.lprof".format(strategy_name))
        stdout_trap = StringIO()
        env.profile_deco.print_stats(stdout_trap)
        profile_output = stdout_trap.getvalue()
        profile_output = profile_output.rstrip()
        print(profile_output)
        env.event_bus.publish_event(Events.ON_LINE_PROFILER_RESULT, profile_output)


def generate_report(result_dict, target_report_csv_path):
    import pandas as pd
    from io import StringIO

    output_path = os.path.join(target_report_csv_path, result_dict["summary"]["strategy_name"])
    try:
        os.mkdir(output_path)
    except:
        pass

    xlsx_writer = pd.ExcelWriter(os.path.join(output_path, "report.xlsx"), engine='xlsxwriter')

    # summary.csv
    csv_txt = StringIO()
    summary = result_dict["summary"]
    csv_txt.write("\n".join(sorted("{},{}".format(key, value) for key, value in iteritems(summary))))
    df = pd.DataFrame(data=[{"val": val} for val in summary.values()], index=summary.keys()).sort_index()
    df.to_excel(xlsx_writer, sheet_name="summary")

    with open(os.path.join(output_path, "summary.csv"), 'w') as csvfile:
        csvfile.write(csv_txt.getvalue())

    for name in ["total_portfolios", "stock_portfolios", "future_portfolios",
                 "stock_positions", "future_positions", "trades"]:
        try:
            df = result_dict[name]
        except KeyError:
            continue

        # replace all date in dataframe as string
        if df.index.name == "date":
            df = df.reset_index()
            df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
            df = df.set_index("date")

        csv_txt = StringIO()
        csv_txt.write(df.to_csv())

        df.to_excel(xlsx_writer, sheet_name=name)

        with open(os.path.join(output_path, "{}.csv".format(name)), 'w') as csvfile:
            csvfile.write(csv_txt.getvalue())

    # report.xls <--- 所有sheet的汇总
    xlsx_writer.save()
