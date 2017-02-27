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

import six
import os
import yaml
import datetime
import logbook
from pprint import pformat
import codecs
import shutil

from . import RqAttrDict, logger
from .exception import patch_user_exc
from .logger import user_log, user_system_log, system_log, std_log, user_std_handler
from ..const import ACCOUNT_TYPE, MATCHING_TYPE, RUN_TYPE, PERSIST_MODE
from ..utils.i18n import gettext as _
from ..utils.dict_func import deep_update
from ..mod.utils import mod_config_value_parse


def parse_config(config_args, base_config_path=None, click_type=True, source_code=None):
    default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../config_template.yml")
    with codecs.open(default_config_path, encoding="utf-8") as f:
        default_config = f.read()
    default_config = yaml.load(default_config)

    if base_config_path is None:
        config_path = os.path.abspath(os.path.expanduser("~/.rqalpha/config.yml"))
        if not os.path.exists(config_path):
            dir_path = os.path.dirname(config_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            open(config_path, "wb").write(open(default_config_path, "rb").read())
    else:
        config_path = base_config_path
    if not os.path.exists(config_path):
        print("config.yaml not found in", os.getcwd())
        return

    with codecs.open(config_path, encoding="utf-8") as f:
        config_file = f.read()

    mod_configs = config_args.pop("mod_configs", [])
    for cfg, value in mod_configs:
        key = "mod__{}".format(cfg.replace(".", "__"))
        config_args[key] = mod_config_value_parse(value)

    config = yaml.load(config_file)
    config_version = config.get("version", None)
    if config_version is None or config_version != default_config["version"]:
        config_file_path = os.path.abspath(config_path)
        back_config_file_path = config_file_path + "." + datetime.datetime.now().date().strftime("%Y%m%d") + ".bak"
        shutil.move(config_file_path, back_config_file_path)
        shutil.copy(default_config_path, config_file_path)

        system_log.warning("""
您使用的配置文件 {config_file_path} 版本过久，可能会导致RQAlpha运行错误。
已为您替换为新的配置文件，
旧的配置文件备份存储于 {back_config_file_path}
        """.format(config_file_path=config_file_path, back_config_file_path=back_config_file_path))
        config = default_config

    if click_type:
        for key, value in six.iteritems(config_args):
            if key in ["config_path"]:
                continue
            if config_args[key] is not None:
                keys = key.split("__")
                keys.reverse()
                sub_config = config[keys.pop()]
                while True:
                    if len(keys) == 0:
                        break
                    k = keys.pop()
                    if len(keys) == 0:
                        sub_config[k] = value
                    else:
                        sub_config = sub_config[k]
    else:
        deep_update(config_args, config)

    config = parse_user_config(config, source_code)

    config = RqAttrDict(config)
    base_config = config.base
    extra_config = config.extra

    if isinstance(base_config.start_date, six.string_types):
        base_config.start_date = datetime.datetime.strptime(base_config.start_date, "%Y-%m-%d")
    if isinstance(base_config.start_date, datetime.datetime):
        base_config.start_date = base_config.start_date.date()
    if isinstance(base_config.end_date, six.string_types):
        base_config.end_date = datetime.datetime.strptime(base_config.end_date, "%Y-%m-%d")
    if isinstance(base_config.end_date, datetime.datetime):
        base_config.end_date = base_config.end_date.date()
    if base_config.commission_multiplier < 0:
        raise patch_user_exc(ValueError(_("invalid commission multiplier value: value range is [0, +∞)")))
    if base_config.margin_multiplier <= 0:
        raise patch_user_exc(ValueError(_("invalid margin multiplier value: value range is (0, +∞]")))

    if base_config.data_bundle_path is None:
        base_config.data_bundle_path = os.path.expanduser("~/.rqalpha")

    base_config.data_bundle_path = os.path.abspath(base_config.data_bundle_path)

    if os.path.basename(base_config.data_bundle_path) != "bundle":
        base_config.data_bundle_path = os.path.join(base_config.data_bundle_path, "./bundle")

    if not os.path.exists(base_config.data_bundle_path):
        print("data bundle not found. Run `rqalpha update_bundle` to download data bundle.")
        # print("data bundle not found. Run `%s update_bundle` to download data bundle." % sys.argv[0])
        return

    if source_code is None and not os.path.exists(base_config.strategy_file):
        print("strategy file not found: ", base_config.strategy_file)
        return

    base_config.run_type = parse_run_type(base_config.run_type)
    base_config.account_list = gen_account_list(base_config.strategy_type)
    base_config.matching_type = parse_matching_type(base_config.matching_type)
    base_config.persist_mode = parse_persist_mode(base_config.persist_mode)

    if extra_config.log_level.upper() != "NONE":
        user_log.handlers.append(user_std_handler)
        if not extra_config.user_system_log_disabled:
            user_system_log.handlers.append(user_std_handler)

    if extra_config.context_vars:
        import base64
        import json
        extra_config.context_vars = json.loads(base64.b64decode(extra_config.context_vars).decode('utf-8'))

    if base_config.stock_starting_cash < 0:
        raise patch_user_exc(ValueError(_('invalid stock starting cash: {}').format(base_config.stock_starting_cash)))

    if base_config.future_starting_cash < 0:
        raise patch_user_exc(ValueError(_('invalid future starting cash: {}').format(base_config.future_starting_cash)))

    if base_config.stock_starting_cash + base_config.future_starting_cash == 0:
        raise patch_user_exc(ValueError(_('stock starting cash and future starting cash can not be both 0.')))

    system_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    std_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    user_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    user_system_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)

    if base_config.frequency == "1d":
        logger.DATETIME_FORMAT = "%Y-%m-%d"
        config.validator.fast_match = True

    system_log.debug("\n" + pformat(config))

    return config


def parse_user_config(config, source_code=None):
    try:
        if source_code is None:
            with codecs.open(config["base"]["strategy_file"], encoding="utf-8") as f:
                source_code = f.read()

        scope = {}

        code = compile(source_code, config["base"]["strategy_file"], 'exec')
        six.exec_(code, scope)

        __config__ = scope.get("__config__", {})

        deep_update(__config__, config)

        for sub_key, sub_dict in six.iteritems(__config__):
            if sub_key not in config["whitelist"]:
                continue
            deep_update(sub_dict, config[sub_key])

    except Exception as e:
        print('in parse_user_config, exception: ', e)
    finally:
        return config


def gen_account_list(account_list_str):
    assert isinstance(account_list_str, six.string_types)
    account_list = account_list_str.split("_")
    return [parse_account_type(account_str) for account_str in account_list]


def parse_account_type(account_type_str):
    assert isinstance(account_type_str, six.string_types)
    if account_type_str == "stock":
        return ACCOUNT_TYPE.STOCK
    elif account_type_str == "future":
        return ACCOUNT_TYPE.FUTURE


def parse_matching_type(me_str):
    assert isinstance(me_str, six.string_types)
    if me_str == "current_bar":
        return MATCHING_TYPE.CURRENT_BAR_CLOSE
    elif me_str == "next_bar":
        return MATCHING_TYPE.NEXT_BAR_OPEN
    else:
        raise NotImplementedError


def parse_run_type(rt_str):
    assert isinstance(rt_str, six.string_types)
    if rt_str == "b":
        return RUN_TYPE.BACKTEST
    elif rt_str == "p":
        return RUN_TYPE.PAPER_TRADING
    elif rt_str == "CTP":
        return RUN_TYPE.CTP
    else:
        raise NotImplementedError


def parse_persist_mode(persist_mode):
    assert isinstance(persist_mode, six.string_types)
    if persist_mode == 'real_time':
        return PERSIST_MODE.REAL_TIME
    elif persist_mode == 'on_crash':
        return PERSIST_MODE.ON_CRASH
    else:
        raise RuntimeError('unknown persist mode: {}'.format(persist_mode))
