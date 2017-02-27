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
import click
import jsonpickle.ext.numpy as jsonpickle_numpy
import pytz
import requests
import six

from . import const
from .api import helper as api_helper
from .core.strategy_loader import FileStrategyLoader, SourceCodeStrategyLoader
from .core.strategy import Strategy
from .core.strategy_universe import StrategyUniverse
from .core.global_var import GlobalVars
from .core.strategy_context import StrategyContext
from .data.base_data_source import BaseDataSource
from .data.data_proxy import DataProxy
from .environment import Environment
from .events import EVENT
from .execution_context import ExecutionContext
from .interface import Persistable
from .mod.mod_handler import ModHandler
from .model.bar import BarMap
from .model.account import MixedAccount
from .utils import create_custom_exception, run_with_user_log_disabled
from .utils.exception import CustomException, is_user_exc, patch_user_exc
from .utils.i18n import gettext as _
from .utils.logger import user_log, user_system_log, system_log, user_print, user_detail_log
from .utils.persisit_helper import CoreObjectsPersistProxy, PersistHelper
from .utils.scheduler import Scheduler
from .utils import scheduler as mod_scheduler


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
    if instrument is None:
        raise patch_user_exc(ValueError(_('invalid benchmark {}').format(benchmark)))

    if instrument.order_book_id == "000300.XSHG":
        # 000300.XSHG 数据进行了补齐，因此认为只要benchmark设置了000300.XSHG，就存在数据，不受限于上市日期。
        return
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


def update_bundle(data_bundle_path=None, confirm=True):
    default_bundle_path = os.path.abspath(os.path.expanduser("~/.rqalpha/bundle/"))
    if data_bundle_path is None:
        data_bundle_path = default_bundle_path
    else:
        data_bundle_path = os.path.abspath(os.path.join(data_bundle_path, './bundle/'))
    if (confirm and os.path.exists(data_bundle_path) and data_bundle_path != default_bundle_path and
            os.listdir(data_bundle_path)):
        click.confirm('[WARNING] Target bundle path {} is not empty. The content of this folder will be REMOVED before '
                      'updating. Are you sure to continue?'.format(data_bundle_path), abort=True)

    day = datetime.date.today()
    tmp = os.path.join(tempfile.gettempdir(), 'rq.bundle')

    while True:
        url = 'http://7xjci3.com1.z0.glb.clouddn.com/bundles_v2/rqbundle_%04d%02d%02d.tar.bz2' % (
            day.year, day.month, day.day)
        six.print_('try {} ...'.format(url))
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            day = day - datetime.timedelta(days=1)
            continue

        out = open(tmp, 'wb')
        total_length = int(r.headers.get('content-length'))

        with click.progressbar(length=total_length, label='downloading ...') as bar:
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


def run(config, source_code=None):
    env = Environment(config)
    persist_helper = None
    init_succeed = False
    mod_handler = ModHandler()

    try:
        env.set_strategy_loader(FileStrategyLoader() if source_code is None else SourceCodeStrategyLoader())
        env.set_global_vars(GlobalVars())
        mod_handler.set_env(env)
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

        broker = env.broker
        assert broker is not None
        env.accounts = accounts = broker.get_accounts()
        env.account = account = MixedAccount(accounts)

        ExecutionContext.broker = broker
        ExecutionContext.accounts = accounts
        ExecutionContext.account = account
        ExecutionContext.config = env.config

        event_source = env.event_source
        assert event_source is not None

        bar_dict = BarMap(env.data_proxy, config.base.frequency)
        ctx = ExecutionContext(const.EXECUTION_PHASE.GLOBAL, bar_dict)
        ctx._push()

        # FIXME
        start_dt = datetime.datetime.combine(config.base.start_date, datetime.datetime.min.time())
        env.calendar_dt = ExecutionContext.calendar_dt = start_dt
        env.trading_dt = ExecutionContext.trading_dt = start_dt

        env.event_bus.publish_event(EVENT.POST_SYSTEM_INIT)

        scope = create_base_scope()
        scope.update({
            "g": env.global_vars
        })

        apis = api_helper.get_apis(config.base.account_list)
        scope.update(apis)

        scope = env.strategy_loader.load(env.config.base.strategy_file if source_code is None else source_code, scope)

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

        if config.base.persist:
            persist_provider = env.persist_provider
            persist_helper = PersistHelper(persist_provider, env.event_bus, config.base.persist_mode)
            persist_helper.register('core', CoreObjectsPersistProxy(scheduler))
            persist_helper.register('user_context', ucontext)
            persist_helper.register('global_vars', env.global_vars)
            persist_helper.register('universe', env._universe)
            if isinstance(event_source, Persistable):
                persist_helper.register('event_source', event_source)
            for k, v in six.iteritems(accounts):
                persist_helper.register('{}_account'.format(k.name.lower()), v)
            for name, module in six.iteritems(env.mod_dict):
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
            with run_with_user_log_disabled(disabled=False):
                user_strategy.init()

        for event in event_source.events(config.base.start_date, config.base.end_date, config.base.frequency):
            calendar_dt = event.calendar_dt
            trading_dt = event.trading_dt
            event_type = event.event_type
            ExecutionContext.calendar_dt = calendar_dt
            ExecutionContext.trading_dt = trading_dt
            env.calendar_dt = calendar_dt
            env.trading_dt = trading_dt
            for account in accounts.values():
                account.portfolio._current_date = trading_dt.date()

            if event_type == EVENT.BEFORE_TRADING:
                env.event_bus.publish_event(EVENT.PRE_BEFORE_TRADING)
                env.event_bus.publish_event(EVENT.BEFORE_TRADING)
                env.event_bus.publish_event(EVENT.POST_BEFORE_TRADING)
            elif event_type == EVENT.BAR:
                bar_dict.update_dt(calendar_dt)
                env.event_bus.publish_event(EVENT.PRE_BAR)
                env.event_bus.publish_event(EVENT.BAR, bar_dict)
                env.event_bus.publish_event(EVENT.POST_BAR)
            elif event_type == EVENT.TICK:
                env.event_bus.publish_event(EVENT.PRE_TICK)
                env.event_bus.publish_event(EVENT.TICK, event.data['tick'])
                env.event_bus.publish_event(EVENT.POST_TICK)
            elif event_type == EVENT.AFTER_TRADING:
                env.event_bus.publish_event(EVENT.PRE_AFTER_TRADING)
                env.event_bus.publish_event(EVENT.AFTER_TRADING)
                env.event_bus.publish_event(EVENT.POST_AFTER_TRADING)
            elif event_type == EVENT.SETTLEMENT:
                env.event_bus.publish_event(EVENT.PRE_SETTLEMENT)
                env.event_bus.publish_event(EVENT.SETTLEMENT)
                env.event_bus.publish_event(EVENT.POST_SETTLEMENT)
            else:
                raise RuntimeError('unknown event from event source: {}'.format(event))

        if env.profile_deco:
            output_profile_result(env)

        mod_handler.tear_down(const.EXIT_CODE.EXIT_SUCCESS)
        system_log.debug("strategy run successfully, normal exit")

        # FIXME
        if 'analyser' in env.mod_dict:
            return env.mod_dict['analyser']._result
    except CustomException as e:
        if init_succeed and env.config.base.persist and persist_helper:
            persist_helper.persist()

        user_detail_log.exception("strategy execute exception")
        user_system_log.error(e.error)
        mod_handler.tear_down(const.EXIT_CODE.EXIT_USER_ERROR, e)
    except Exception as e:
        if init_succeed and env.config.base.persist and persist_helper:
            persist_helper.persist()

        exc_type, exc_val, exc_tb = sys.exc_info()
        user_exc = create_custom_exception(exc_type, exc_val, exc_tb, config.base.strategy_file)

        user_system_log.error(user_exc.error)
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
            for key, val in six.iteritems(obj.__dict__):
                if inspect.isfunction(val):
                    setattr(obj, key, profile_deco(val))


def output_profile_result(env):
    from six import StringIO
    stdout_trap = StringIO()
    env.profile_deco.print_stats(stdout_trap)
    profile_output = stdout_trap.getvalue()
    profile_output = profile_output.rstrip()
    print(profile_output)
    env.event_bus.publish_event(EVENT.ON_LINE_PROFILER_RESULT, profile_output)
