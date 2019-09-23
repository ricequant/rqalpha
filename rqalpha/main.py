# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import sys
import datetime
from pprint import pformat

import logbook
import jsonpickle.ext.numpy as jsonpickle_numpy
import pytz
import six

from rqalpha import const
from rqalpha.api import helper as api_helper
from rqalpha.core.strategy_loader import FileStrategyLoader, SourceCodeStrategyLoader, UserFuncStrategyLoader
from rqalpha.core.strategy import Strategy
from rqalpha.core.strategy_universe import StrategyUniverse
from rqalpha.core.global_var import GlobalVars
from rqalpha.core.strategy_context import StrategyContext
from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.data.data_proxy import DataProxy
from rqalpha.environment import Environment
from rqalpha.events import EVENT, Event
from rqalpha.execution_context import ExecutionContext
from rqalpha.interface import Persistable
from rqalpha.mod import ModHandler
from rqalpha.model.bar import BarMap
from rqalpha.model.benchmark_portfolio import BenchmarkPortfolio
from rqalpha.const import RUN_TYPE
from rqalpha.utils import create_custom_exception, run_with_user_log_disabled, scheduler as mod_scheduler, RqAttrDict
from rqalpha.utils.exception import CustomException, is_user_exc, patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.persisit_helper import CoreObjectsPersistProxy, PersistHelper
from rqalpha.utils.scheduler import Scheduler
from rqalpha.utils.logger import system_log, basic_system_log, user_system_log, user_detail_log


jsonpickle_numpy.register_handlers()


def _adjust_start_date(config, data_proxy):
    origin_start_date, origin_end_date = config.base.start_date, config.base.end_date
    start, end = data_proxy.available_data_range(config.base.frequency)

    config.base.start_date = max(start, config.base.start_date)
    config.base.end_date = min(end, config.base.end_date)

    config.base.trading_calendar = data_proxy.get_trading_dates(config.base.start_date, config.base.end_date)
    if len(config.base.trading_calendar) == 0:
        raise patch_user_exc(
            ValueError(
                _(u"There is no data between {start_date} and {end_date}. Please check your"
                  u" data bundle or select other backtest period.").format(
                      start_date=origin_start_date, end_date=origin_end_date)))
    config.base.start_date = config.base.trading_calendar[0].date()
    config.base.end_date = config.base.trading_calendar[-1].date()
    config.base.timezone = pytz.utc


def create_base_scope(copy_scope=False):
    from rqalpha.utils.logger import user_print, user_log
    from . import user_module

    if copy_scope:
        from copy import copy
        scope = copy(user_module.__dict__)
    else:
        scope = user_module.__dict__
    scope.update({
        "logger": user_log,
        "print": user_print,
    })

    return scope


def init_persist_helper(env, scheduler, ucontext, executor, config):
    if not config.base.persist:
        return None
    persist_provider = env.persist_provider
    if persist_provider is None:
        raise RuntimeError(_(u"Missing persist provider. You need to set persist_provider before use persist"))
    persist_helper = PersistHelper(persist_provider, env.event_bus, config.base.persist_mode)
    env.set_persist_helper(persist_helper)
    persist_helper.register('core', CoreObjectsPersistProxy(scheduler))
    persist_helper.register('user_context', ucontext)
    persist_helper.register('global_vars', env.global_vars)
    persist_helper.register('universe', env._universe)
    if isinstance(env.event_source, Persistable):
        persist_helper.register('event_source', env.event_source)
    persist_helper.register('portfolio', env.portfolio)
    for name, module in six.iteritems(env.mod_dict):
        if isinstance(module, Persistable):
            persist_helper.register('mod_{}'.format(name), module)
    # broker will restore open orders from account
    if isinstance(env.broker, Persistable):
        persist_helper.register('broker', env.broker)
    persist_helper.register('executor', executor)
    return persist_helper


def init_strategy_loader(env, source_code, user_funcs, config):
    if source_code is not None:
        return SourceCodeStrategyLoader(source_code)
    elif user_funcs is not None:
        return UserFuncStrategyLoader(user_funcs)
    else:
        return FileStrategyLoader(config.base.strategy_file)


def run(config, source_code=None, user_funcs=None):
    env = Environment(config)
    persist_helper = None
    init_succeed = False
    mod_handler = ModHandler()

    try:
        # avoid register handlers everytime
        # when running in ipython
        set_loggers(config)
        basic_system_log.debug("\n" + pformat(config.convert_to_dict()))

        env.set_strategy_loader(init_strategy_loader(env, source_code, user_funcs, config))
        env.set_global_vars(GlobalVars())
        mod_handler.set_env(env)
        mod_handler.start_up()

        if not env.data_source:
            env.set_data_source(BaseDataSource(config.base.data_bundle_path, getattr(config.base, "future_info", {})))

        if env.price_board is None:
            from rqalpha.data.bar_dict_price_board import BarDictPriceBoard
            env.price_board = BarDictPriceBoard()

        env.set_data_proxy(DataProxy(env.data_source, env.price_board))

        Scheduler.set_trading_dates_(env.data_source.get_trading_calendar())
        scheduler = Scheduler(config.base.frequency)
        mod_scheduler._scheduler = scheduler

        env._universe = StrategyUniverse()

        _adjust_start_date(env.config, env.data_proxy)

        # FIXME
        start_dt = datetime.datetime.combine(config.base.start_date, datetime.datetime.min.time())
        env.calendar_dt = start_dt
        env.trading_dt = start_dt

        broker = env.broker
        assert broker is not None
        env.portfolio = broker.get_portfolio()
        if env.benchmark_provider:
            env.benchmark_portfolio = BenchmarkPortfolio(env.benchmark_provider, env.portfolio.units)

        event_source = env.event_source
        assert event_source is not None

        bar_dict = BarMap(env.data_proxy, config.base.frequency)
        env.set_bar_dict(bar_dict)

        ctx = ExecutionContext(const.EXECUTION_PHASE.GLOBAL)
        ctx._push()

        env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))

        scope = create_base_scope(config.base.run_type == RUN_TYPE.BACKTEST)
        scope.update({
            "g": env.global_vars
        })

        apis = api_helper.get_apis()
        scope.update(apis)

        scope = env.strategy_loader.load(scope)

        if env.config.extra.enable_profiler:
            enable_profiler(env, scope)

        ucontext = StrategyContext()
        scheduler.set_user_context(ucontext)

        from .core.executor import Executor
        executor = Executor(env)

        persist_helper = init_persist_helper(env, scheduler, ucontext, executor, config)

        if persist_helper:
            should_resume = persist_helper.should_resume()
            should_run_init = persist_helper.should_run_init()
        else:
            should_resume = False
            should_run_init = True

        user_strategy = Strategy(env.event_bus, scope, ucontext, should_run_init)
        env.user_strategy = user_strategy

        if (should_resume and not should_run_init) or not should_resume:
            with run_with_user_log_disabled(disabled=should_resume):
                user_strategy.init()

        if config.extra.context_vars:
            for k, v in six.iteritems(config.extra.context_vars):
                if isinstance(v, RqAttrDict):
                    v = v.__dict__
                setattr(ucontext, k, v)

        if persist_helper:
            env.event_bus.publish_event(Event(EVENT.BEFORE_SYSTEM_RESTORED))
            env.event_bus.publish_event(Event(EVENT.DO_RESTORE))
            env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_RESTORED))

        init_succeed = True

        if should_resume and should_run_init:
            user_strategy.init()

        executor.run(bar_dict)

        if env.profile_deco:
            output_profile_result(env)
    except CustomException as e:
        if init_succeed and persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_CRASH:
            persist_helper.persist()

        code = _exception_handler(e)
        mod_handler.tear_down(code, e)
    except Exception as e:
        if init_succeed and persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_CRASH:
            persist_helper.persist()

        exc_type, exc_val, exc_tb = sys.exc_info()
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, config.base.strategy_file)

        code = _exception_handler(user_exc)
        mod_handler.tear_down(code, user_exc)
    else:
        if persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_NORMAL_EXIT:
            persist_helper.persist()
        result = mod_handler.tear_down(const.EXIT_CODE.EXIT_SUCCESS)
        system_log.debug(_(u"strategy run successfully, normal exit"))
        return result


def _exception_handler(e):
    try:
        sys.excepthook(e.error.exc_type, e.error.exc_val, e.error.exc_tb)
    except Exception as e:
        system_log.exception("hook exception failed")

    user_system_log.error(e.error)
    if not is_user_exc(e.error.exc_val):
        code = const.EXIT_CODE.EXIT_INTERNAL_ERROR
        system_log.error(_(u"strategy execute exception"), exc=e)
    else:
        code = const.EXIT_CODE.EXIT_USER_ERROR
        user_detail_log.error(_(u"strategy execute exception"), exc=e)

    return code


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
            for key, val in six.iteritems(obj.__dict__):
                if inspect.isfunction(val):
                    setattr(obj, key, profile_deco(val))


def output_profile_result(env):
    stdout_trap = six.StringIO()
    env.profile_deco.print_stats(stdout_trap)
    profile_output = stdout_trap.getvalue()
    profile_output = profile_output.rstrip()
    six.print_(profile_output)
    env.event_bus.publish_event(Event(EVENT.ON_LINE_PROFILER_RESULT, result=profile_output))


def set_loggers(config):
    from rqalpha.utils.logger import user_log, user_system_log, user_detail_log, system_log, basic_system_log, std_log
    from rqalpha.utils.logger import user_std_handler, init_logger
    from rqalpha.utils import logger
    extra_config = config.extra

    init_logger()

    for log in [basic_system_log, system_log, std_log, user_system_log, user_detail_log]:
        log.level = getattr(logbook, config.extra.log_level.upper(), logbook.NOTSET)

    user_log.level = logbook.DEBUG

    if extra_config.log_level.upper() != "NONE":
        if not extra_config.user_log_disabled:
            user_log.handlers.append(user_std_handler)
        if not extra_config.user_system_log_disabled:
            user_system_log.handlers.append(user_std_handler)

    for logger_name, level in extra_config.logger:
        getattr(logger, logger_name).level = getattr(logbook, level.upper())
