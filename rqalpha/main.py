# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
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
import tarfile
import tempfile
import datetime
import shutil
from pprint import pformat

import logbook
import click
import jsonpickle.ext.numpy as jsonpickle_numpy
import pytz
import requests
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
from rqalpha.model.portfolio import Portfolio
from rqalpha.model.base_position import Positions
from rqalpha.utils import create_custom_exception, run_with_user_log_disabled, scheduler as mod_scheduler
from rqalpha.utils.exception import CustomException, is_user_exc, patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.persisit_helper import CoreObjectsPersistProxy, PersistHelper
from rqalpha.utils.scheduler import Scheduler
from rqalpha.utils.config import set_locale
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


def _validate_benchmark(config, data_proxy):
    benchmark = config.base.benchmark
    if benchmark is None:
        return
    instrument = data_proxy.instruments(benchmark)
    if instrument is None:
        raise patch_user_exc(ValueError(_(u"invalid benchmark {}").format(benchmark)))

    if instrument.order_book_id == "000300.XSHG":
        # 000300.XSHG 数据进行了补齐，因此认为只要benchmark设置了000300.XSHG，就存在数据，不受限于上市日期。
        return
    config = Environment.get_instance().config
    start_date = config.base.start_date
    end_date = config.base.end_date
    if instrument.listed_date.date() > start_date:
        raise patch_user_exc(ValueError(
            _(u"benchmark {benchmark} has not been listed on {start_date}").format(benchmark=benchmark,
                                                                                   start_date=start_date)))
    if instrument.de_listed_date.date() < end_date:
        raise patch_user_exc(ValueError(
            _(u"benchmark {benchmark} has been de_listed on {end_date}").format(benchmark=benchmark,
                                                                                end_date=end_date)))


def create_benchmark_portfolio(env):
    if env.config.base.benchmark is None:
        return None

    BenchmarkAccount = env.get_account_model(const.DEFAULT_ACCOUNT_TYPE.BENCHMARK.name)
    BenchmarkPosition = env.get_position_model(const.DEFAULT_ACCOUNT_TYPE.BENCHMARK.name)

    start_date = env.config.base.start_date
    total_cash = sum(env.config.base.accounts.values())
    accounts = {
        const.DEFAULT_ACCOUNT_TYPE.BENCHMARK.name: BenchmarkAccount(total_cash, Positions(BenchmarkPosition))
    }
    return Portfolio(start_date, 1, total_cash, accounts)


def create_base_scope():
    import copy
    from rqalpha.utils.logger import user_print, user_log

    from . import user_module
    scope = copy.copy(user_module.__dict__)
    scope.update({
        "logger": user_log,
        "print": user_print,
    })

    return scope


def update_bundle(data_bundle_path=None, locale="zh_Hans_CN", confirm=True):
    set_locale(locale)
    default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))
    if data_bundle_path is None:
        data_bundle_path = default_bundle_path
    else:
        data_bundle_path = os.path.abspath(os.path.join(data_bundle_path, './bundle/'))
    if (confirm and os.path.exists(data_bundle_path) and data_bundle_path != default_bundle_path and
            os.listdir(data_bundle_path)):
        click.confirm(_(u"""
[WARNING]
Target bundle path {data_bundle_path} is not empty.
The content of this folder will be REMOVED before updating.
Are you sure to continue?""").format(data_bundle_path=data_bundle_path), abort=True)

    day = datetime.date.today()
    tmp = os.path.join(tempfile.gettempdir(), 'rq.bundle')

    while True:
        url = 'http://7xjci3.com1.z0.glb.clouddn.com/bundles_v3/rqbundle_%04d%02d%02d.tar.bz2' % (
            day.year, day.month, day.day)
        six.print_(_(u"try {} ...").format(url))
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            day = day - datetime.timedelta(days=1)
            continue

        out = open(tmp, 'wb')
        total_length = int(r.headers.get('content-length'))

        with click.progressbar(length=total_length, label=_(u"downloading ...")) as bar:
            for data in r.iter_content(chunk_size=8192):
                bar.update(len(data))
                out.write(data)

        out.close()
        break

    shutil.rmtree(data_bundle_path, ignore_errors=True)
    os.makedirs(data_bundle_path)
    tar = tarfile.open(tmp, 'r:bz2')
    tar.extractall(data_bundle_path)
    tar.close()
    os.remove(tmp)
    six.print_(_(u"Data bundle download successfully in {bundle_path}").format(bundle_path=data_bundle_path))


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

        if source_code is not None:
            env.set_strategy_loader(SourceCodeStrategyLoader(source_code))
        elif user_funcs is not None:
            env.set_strategy_loader(UserFuncStrategyLoader(user_funcs))
        else:
            env.set_strategy_loader(FileStrategyLoader(config.base.strategy_file))
        env.set_global_vars(GlobalVars())
        mod_handler.set_env(env)
        mod_handler.start_up()

        if not env.data_source:
            env.set_data_source(BaseDataSource(config.base.data_bundle_path))
        env.set_data_proxy(DataProxy(env.data_source))

        Scheduler.set_trading_dates_(env.data_source.get_trading_calendar())
        scheduler = Scheduler(config.base.frequency)
        mod_scheduler._scheduler = scheduler

        env._universe = StrategyUniverse()

        _adjust_start_date(env.config, env.data_proxy)

        _validate_benchmark(env.config, env.data_proxy)

        # FIXME
        start_dt = datetime.datetime.combine(config.base.start_date, datetime.datetime.min.time())
        env.calendar_dt = start_dt
        env.trading_dt = start_dt

        broker = env.broker
        assert broker is not None
        env.portfolio = broker.get_portfolio()
        env.benchmark_portfolio = create_benchmark_portfolio(env)

        event_source = env.event_source
        assert event_source is not None

        bar_dict = BarMap(env.data_proxy, config.base.frequency)
        env.set_bar_dict(bar_dict)

        if env.price_board is None:
            from .core.bar_dict_price_board import BarDictPriceBoard
            env.price_board = BarDictPriceBoard()

        ctx = ExecutionContext(const.EXECUTION_PHASE.GLOBAL)
        ctx._push()

        env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))

        scope = create_base_scope()
        scope.update({
            "g": env.global_vars
        })

        apis = api_helper.get_apis()
        scope.update(apis)

        scope = env.strategy_loader.load(scope)

        if env.config.extra.enable_profiler:
            enable_profiler(env, scope)

        ucontext = StrategyContext()
        user_strategy = Strategy(env.event_bus, scope, ucontext)
        scheduler.set_user_context(ucontext)

        if not config.extra.force_run_init_when_pt_resume:
            with run_with_user_log_disabled(disabled=config.base.resume_mode):
                user_strategy.init()

        if config.extra.context_vars:
            for k, v in six.iteritems(config.extra.context_vars):
                setattr(ucontext, k, v)

        from .core.executor import Executor
        executor = Executor(env)

        if config.base.persist:
            persist_provider = env.persist_provider
            if persist_provider is None:
                raise RuntimeError(_(u"Missing persist provider. You need to set persist_provider before use persist"))
            persist_helper = PersistHelper(persist_provider, env.event_bus, config.base.persist_mode)
            env.set_persist_helper(persist_helper)
            persist_helper.register('core', CoreObjectsPersistProxy(scheduler))
            persist_helper.register('user_context', ucontext)
            persist_helper.register('global_vars', env.global_vars)
            persist_helper.register('universe', env._universe)
            if isinstance(event_source, Persistable):
                persist_helper.register('event_source', event_source)
            persist_helper.register('portfolio', env.portfolio)
            if env.benchmark_portfolio:
                persist_helper.register('benchmark_portfolio', env.benchmark_portfolio)
            for name, module in six.iteritems(env.mod_dict):
                if isinstance(module, Persistable):
                    persist_helper.register('mod_{}'.format(name), module)
            # broker will restore open orders from account
            if isinstance(broker, Persistable):
                persist_helper.register('broker', broker)
            persist_helper.register('executor', executor)

            env.event_bus.publish_event(Event(EVENT.BEFORE_SYSTEM_RESTORED))
            persist_helper.restore()
            env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_RESTORED))

        init_succeed = True

        # When force_run_init_when_pt_resume is active,
        # we should run `init` after restore persist data
        if config.extra.force_run_init_when_pt_resume:
            assert config.base.resume_mode == True
            with run_with_user_log_disabled(disabled=False):
                env._universe._set = set()
                user_strategy.init()

        executor.run(bar_dict)

        if env.profile_deco:
            output_profile_result(env)
    except CustomException as e:
        if init_succeed and env.config.base.persist and persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_CRASH:
            persist_helper.persist()

        code = _exception_handler(e)
        mod_handler.tear_down(code, e)
    except Exception as e:
        if init_succeed and env.config.base.persist and persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_CRASH:
            persist_helper.persist()

        exc_type, exc_val, exc_tb = sys.exc_info()
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, config.base.strategy_file)

        code = _exception_handler(user_exc)
        mod_handler.tear_down(code, user_exc)
    else:
        if (env.config.base.persist and persist_helper and env.config.base.persist_mode == const.PERSIST_MODE.ON_NORMAL_EXIT):
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
