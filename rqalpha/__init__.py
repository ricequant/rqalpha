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

"""
RQAlpha - a Algorithm Trading System
"""
from typing import Optional

from rqalpha.cmds import cli, inject_run_param
from rqalpha.api import export_as_api
from rqalpha.apis import subscribe_event
from . import data
from . import interface
from . import portfolio
from . import apis

__all__ = [
    '__version__',
]


def load_ipython_extension(ipython):
    """call by ipython"""
    from rqalpha.mod.utils import inject_mod_commands
    inject_mod_commands()

    ipython.register_magic_function(run_ipython_cell, 'line_cell', 'rqalpha')


def run(config, source_code=None):
    # [Deprecated]
    from rqalpha.utils.config import parse_config
    from rqalpha import main

    config = parse_config(config, source_code=source_code)
    return main.run(config, source_code=source_code)


def run_ipython_cell(line, cell=None):
    from rqalpha.cmds.run import run
    from rqalpha.utils.functools import clear_all_cached_functions
    clear_all_cached_functions()
    args = line.split()
    args.extend(["--source-code", cell if cell is not None else ""])
    try:
        # It raise exception every time
        run.main(args, standalone_mode=True)
    except SystemExit as e:
        pass


def run_file(strategy_file_path, config=None):
    # type: (str, Optional[dict]) -> dict
    """
    传入策略文件路径运行回测。

    :param strategy_file_path: 策略文件路径
    :param config: 策略配置项字典，默认为空，此处传入的配置项优先级高于策略内 :code:`__config__` 中的配置项

    :example:

    .. code-block:: python

        config = {
            "base": {
                ...
            }
        }

        run_file("strategy.py", config=config)

    """
    from rqalpha.utils.config import parse_config
    from rqalpha.utils.functools import clear_all_cached_functions
    from rqalpha import main

    if config is None:
        config = {
            "base": {
                "strategy_file": strategy_file_path
            }
        }
    else:
        assert isinstance(config, dict)
        if "base" in config:
            config["base"]["strategy_file"] = strategy_file_path
        else:
            config["base"] = {
                "strategy_file": strategy_file_path
            }
    config = parse_config(config)
    clear_all_cached_functions()
    return main.run(config)


def run_code(code, config=None):
    # type: (str, Optional[dict]) -> dict
    """
    传入字符串形式的策略代码以运行回测。

    :param code: 策略代码字符串
    :param config:  策略配置项字典，默认为空，此处传入的配置项优先级高于策略内 :code:`__config__` 中的配置项

    :example:

    .. code-block:: python

        config = {
            "base": {
                ...
            }
        }

        CODE = \"\"\"
        def init(context):
            ...

        def handle_bar(context, bar_dict):
            ...
        \"\"\"

        run_code(CODE, config=config)
    """
    from rqalpha.utils.config import parse_config
    from rqalpha.utils.functools import clear_all_cached_functions
    from rqalpha import main

    if config is None:
        config = {}
    else:
        assert isinstance(config, dict)
        try:
            del config["base"]["strategy_file"]
        except:
            pass
    config = parse_config(config, source_code=code)
    clear_all_cached_functions()
    return main.run(config, source_code=code)


def run_func(**kwargs):
    """
    传入约定函数和策略配置运行回测。约定函数详见 API 手册约定函数部分，可用的配置项详见参数配置部分。

    :Keyword Arguments:
        * **config** (dict) -- 策略配置字典
        * **init** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`], Any]) -- 策略初始化函数，会在策略开始运行时被调用，仅会执行一次
        * **before_trading** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`], Any]) -- 盘前函数，会在每日盘前被调用一次
        * **open_auction** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`, dict[str, :class:`~rqalpha.model.bar.BarObject`]], Any]) -- 集合竞价函数，会在每日盘前集合竞价阶段被调用一次
        * **handle_bar** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`, dict[str, :class:`~rqalpha.model.bar.BarObject`]], Any]) -- k 线处理函数，会在盘中 k 线发生更新时被调用，适用于日/分钟级别回测
        * **handle_tick** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`, :class:`~rqalpha.model.tick.TickObject`], Any]) -- 快照数据处理函数，会在每个 tick 到达时被调用，适用于 tick 回测
        * **after_trading** (Callable[[:class:`~rqalpha.core.strategy_context.StrategyContext`], Any]) -- 盘后函数，会在每日交易结束后被调用一次

    :return: dict

    :example:

    .. code-block:: python

        config = {
            "base": {
                ...
            }
        }

        def init(context):
            ...

        def handle_bar(context, bar_dict):
            ...

        run_func(config=config, init=init, handle_bar=handle_bar)

    """
    from rqalpha.utils.functools import clear_all_cached_functions
    from rqalpha.utils.config import parse_config
    from rqalpha import main

    config = kwargs.get('config', kwargs.get('__config__', None))
    user_funcs = {
        k: kwargs[k]
        for k in ['init', 'handle_bar', 'handle_tick', 'open_auction', 'before_trading', 'after_trading']
        if k in kwargs
    }

    if config is None:
        config = {}
    else:
        assert isinstance(config, dict)
        try:
            del config["base"]["strategy_file"]
        except:
            pass
    config = parse_config(config, user_funcs=user_funcs)
    clear_all_cached_functions()
    return main.run(config, user_funcs=user_funcs)


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

version_info = tuple(int(v) if v.isdigit() else v for v in __version__.split('.'))
try:
    __main_version__ = "%s.%s.x" % (version_info[0], version_info[1])
except:
    __main_version__ = "0.0"