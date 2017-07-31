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

"""
RQAlpha - a Algorithm Trading System
"""

import pkgutil

from rqalpha.__main__ import cli
from rqalpha.api.api_base import export_as_api

__all__ = [
    '__version__',
    'version_info'
]

__version__ = pkgutil.get_data(__package__, 'VERSION.txt').decode('ascii').strip()

version_info = tuple(int(v) if v.isdigit() else v
                     for v in __version__.split('.'))

__main_version__ = "%s.%s.x" % (version_info[0], version_info[1])

del pkgutil


def load_ipython_extension(ipython):
    """call by ipython"""
    from rqalpha.__main__ import inject_mod_commands
    inject_mod_commands()

    ipython.register_magic_function(run_ipython_cell, 'line_cell', 'rqalpha')


def update_bundle(data_bundle_path=None, locale="zh_Hans_CN", confirm=True):
    from rqalpha import main
    main.update_bundle(data_bundle_path=data_bundle_path, locale=locale, confirm=confirm)


def run(config, source_code=None):
    # [Deprecated]
    from rqalpha.utils.config import parse_config
    from rqalpha import main

    config = parse_config(config, source_code=source_code)
    return main.run(config, source_code=source_code)


def run_ipython_cell(line, cell=None):
    from rqalpha.__main__ import run
    from rqalpha.utils.py2 import clear_all_cached_functions
    clear_all_cached_functions()
    args = line.split()
    args.extend(["--source-code", cell if cell is not None else ""])
    try:
        # It raise exception every time
        run.main(args, standalone_mode=True)
    except SystemExit as e:
        pass


def run_file(strategy_file_path, config=None):
    from rqalpha.utils.config import parse_config
    from rqalpha.utils.py2 import clear_all_cached_functions
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
    from rqalpha.utils.config import parse_config
    from rqalpha.utils.py2 import clear_all_cached_functions
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
    from rqalpha.utils import dummy_func
    from rqalpha.utils.py2 import clear_all_cached_functions
    from rqalpha.utils.config import parse_config
    from rqalpha import main

    config = kwargs.get('config', kwargs.get('__config__', None))

    user_funcs = {
        'init': kwargs.get('init', dummy_func),
        'handle_bar': kwargs.get('handle_bar', dummy_func),
        'handle_tick': kwargs.get('handle_tick', dummy_func),
        'before_trading': kwargs.get('before_trading', dummy_func),
        'after_trading': kwargs.get('after_trading', dummy_func)
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


def subscribe_event(event_type, handler):
    import types
    from rqalpha.events import EVENT
    from rqalpha.environment import Environment

    assert isinstance(handler, types.FunctionType)
    assert isinstance(event_type, EVENT)

    env = Environment.get_instance()
    env.event_bus.add_listener(event_type, handler)
