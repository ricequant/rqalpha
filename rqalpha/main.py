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

import datetime
import sys
from pprint import pformat
from itertools import chain

import jsonpickle.ext.numpy as jsonpickle_numpy
import logbook
import six
from rqalpha import const
from rqalpha.core.executor import Executor
from rqalpha.core.strategy import Strategy
from rqalpha.core.strategy_context import StrategyContext
from rqalpha.core.strategy_loader import FileStrategyLoader, SourceCodeStrategyLoader, UserFuncStrategyLoader
from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.data.data_proxy import DataProxy
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.interface import Persistable
from rqalpha.mod import ModHandler
from rqalpha.model.bar import BarMap
from rqalpha.utils import RqAttrDict, create_custom_exception, init_rqdatac_env
from rqalpha.utils.exception import CustomException, is_user_exc, patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.log_capture import LogCapture
from rqalpha.utils.logger import release_print, system_log, user_log, user_system_log
from rqalpha.utils.persisit_helper import PersistHelper

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


def create_base_scope():
    from . import user_module
    from copy import copy

    return copy(user_module.__dict__)


def init_persist_helper(env, ucontext, executor, config):
    if not config.base.persist:
        return None
    persist_provider = env.persist_provider
    if persist_provider is None:
        raise RuntimeError(_(u"Missing persist provider. You need to set persist_provider before use persist"))
    persist_helper = PersistHelper(persist_provider, env.event_bus, config.base.persist_mode)
    for key, obj in chain([
        ('user_context', ucontext),
        ('global_vars', env.global_vars),
        ('universe', env._universe),
        ('portfolio', env.portfolio),
        ('executor', executor),
    ], ((key, obj) for key, obj in [
        ('event_source', env.event_source),
        ('broker', env.broker)
    ] if isinstance(obj, Persistable)), ((
        "mod_{}".format(name), mod
    ) for name, mod in env.mod_dict.items() if isinstance(mod, Persistable))):
        persist_helper.register(key, obj)
    env.set_persist_helper(persist_helper)
    return persist_helper


def init_strategy_loader(env, source_code, user_funcs, config):
    if source_code is not None:
        return SourceCodeStrategyLoader(source_code)
    elif user_funcs is not None:
        return UserFuncStrategyLoader(user_funcs)
    else:
        return FileStrategyLoader(config.base.strategy_file)


def get_strategy_apis():
    from rqalpha import api
    return {n: getattr(api, n) for n in api.__all__}


def init_rqdatac(rqdatac_uri):
    try:
        import rqdatac
    except ImportError:
        return

    import warnings

    try:
        init_rqdatac_env(rqdatac_uri)
        with warnings.catch_warnings(record=True):
            rqdatac.init()
    except Exception as e:
        system_log.warn(_('rqdatac init failed, some apis will not function properly: {}').format(str(e)))


def run(config, source_code=None, user_funcs=None):
    env = Environment(config)
    persist_helper = None
    init_succeed = False
    mod_handler = ModHandler()

    try:
        # avoid register handlers everytime
        # when running in ipython
        set_loggers(config)
        init_rqdatac(getattr(config.base, 'rqdatac_uri', None))
        system_log.debug("\n" + pformat(config.convert_to_dict()))

        env.set_strategy_loader(init_strategy_loader(env, source_code, user_funcs, config))
        mod_handler.set_env(env)
        mod_handler.start_up()

        if not env.data_source:
            env.set_data_source(BaseDataSource(config.base.data_bundle_path, getattr(config.base, "future_info", {})))
        if env.price_board is None:
            from rqalpha.data.bar_dict_price_board import BarDictPriceBoard
            env.price_board = BarDictPriceBoard()
        env.set_data_proxy(DataProxy(env.data_source, env.price_board))

        _adjust_start_date(env.config, env.data_proxy)

        ctx = ExecutionContext(const.EXECUTION_PHASE.GLOBAL)
        ctx._push()

        # FIXME
        start_dt = datetime.datetime.combine(config.base.start_date, datetime.datetime.min.time())
        env.calendar_dt = start_dt
        env.trading_dt = start_dt

        assert env.broker is not None
        assert env.event_source is not None
        if env.portfolio is None:
            from rqalpha.portfolio import Portfolio
            env.set_portfolio(Portfolio(config.base.accounts, config.base.init_positions))

        env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))

        scope = create_base_scope()
        scope.update({"g": env.global_vars})
        scope.update(get_strategy_apis())
        scope = env.strategy_loader.load(scope)

        if config.extra.enable_profiler:
            enable_profiler(env, scope)

        ucontext = StrategyContext()
        executor = Executor(env)

        persist_helper = init_persist_helper(env, ucontext, executor, config)
        user_strategy = Strategy(env.event_bus, scope, ucontext)
        env.user_strategy = user_strategy

        env.event_bus.publish_event(Event(EVENT.BEFORE_STRATEGY_RUN))
        if persist_helper:
            with LogCapture(user_log) as log_capture:
                user_strategy.init()
        else:
            user_strategy.init()

        if config.extra.context_vars:
            for k, v in config.extra.context_vars.items():
                if isinstance(v, RqAttrDict):
                    v = v.__dict__
                setattr(ucontext, k, v)

        if persist_helper:
            env.event_bus.publish_event(Event(EVENT.BEFORE_SYSTEM_RESTORED))
            restored_obj_state = persist_helper.restore(None)
            check_key = ["global_vars", "user_context", "executor", "universe"]
            kept_current_init_data = not any(v for k, v in restored_obj_state.items() if k in check_key)
            system_log.debug("restored_obj_state: {}".format(restored_obj_state))
            system_log.debug("kept_current_init_data: {}".format(kept_current_init_data))
            if kept_current_init_data:
                # 未能恢复init相关数据 保留当前策略初始化变量(展示当前策略初始化日志)
                log_capture.replay()
            else:
                user_system_log.info(_('system restored'))
            env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_RESTORED))

        init_succeed = True

        bar_dict = BarMap(env.data_proxy, config.base.frequency)
        executor.run(bar_dict)
        env.event_bus.publish_event(Event(EVENT.POST_STRATEGY_RUN))

        if env.profile_deco:
            output_profile_result(env)
        release_print(scope)
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
    user_system_log.exception(_(u"strategy execute exception"))
    user_system_log.error(e.error)
    if not is_user_exc(e.error.exc_val):
        return const.EXIT_CODE.EXIT_INTERNAL_ERROR

    return const.EXIT_CODE.EXIT_USER_ERROR


def enable_profiler(env, scope):
    # decorate line profiler
    try:
        import line_profiler
    except ImportError:
        raise RuntimeError('--enable-profiler needs line_profiler')

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


def output_profile_result(env):
    stdout_trap = six.StringIO()
    env.profile_deco.print_stats(stdout_trap)
    profile_output = stdout_trap.getvalue()
    profile_output = profile_output.rstrip()
    six.print_(profile_output)
    env.event_bus.publish_event(Event(EVENT.ON_LINE_PROFILER_RESULT, result=profile_output))


def set_loggers(config):
    from rqalpha.utils.logger import user_log, user_system_log, system_log
    from rqalpha.utils.logger import init_logger
    from rqalpha.utils import logger
    extra_config = config.extra

    init_logger()

    for log in [system_log, user_system_log]:
        log.level = getattr(logbook, config.extra.log_level.upper(), logbook.NOTSET)

    user_log.level = logbook.DEBUG

    for logger_name, level in extra_config.logger:
        getattr(logger, logger_name).level = getattr(logbook, level.upper())
