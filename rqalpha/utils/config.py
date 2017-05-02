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
import simplejson as json
import datetime
import logbook
import locale
import codecs
import shutil
from pprint import pformat

from . import RqAttrDict, logger
from .exception import patch_user_exc
from .logger import user_log, user_system_log, system_log, std_log, user_std_handler
from ..const import RUN_TYPE, PERSIST_MODE, ACCOUNT_TYPE
from ..utils.i18n import gettext as _, localization
from ..utils.dict_func import deep_update
from ..utils.py2 import to_utf8
from ..mod.utils import mod_config_value_parse


def load_config(config_path, loader=yaml.Loader):
    if config_path is None:
        return {}
    if not os.path.exists(config_path):
        system_log.error(_(u"config.yml not found in {config_path}").format(config_path))
        return False
    if ".json" in config_path:
        with codecs.open(config_path, encoding="utf-8") as f:
            json_config = f.read()
        config = json.loads(json_config)
    else:
        with codecs.open(config_path, encoding="utf-8") as stream:
            config = yaml.load(stream, loader)
    return config


def dump_config(config_path, config, dumper=yaml.Dumper):
    with codecs.open(config_path, mode='w', encoding='utf-8') as stream:
        stream.write(to_utf8(yaml.dump(config, Dumper=dumper)))


def load_mod_config(config_path, loader=yaml.Loader):
    mod_config = load_config(config_path, loader)
    if mod_config is None or "mod" not in mod_config:
        import os
        os.remove(config_path)
        config_path = get_mod_config_path()
        return load_mod_config(config_path, loader)
    else:
        return mod_config


def get_mod_config_path(generate=False):
    mod_config_path = os.path.abspath(os.path.expanduser("~/.rqalpha/mod_config.yml"))
    mod_template_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../mod_config_template.yml"))
    if not os.path.exists(mod_config_path):
        if generate:
            dir_path = os.path.dirname(mod_config_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            shutil.copy(mod_template_path, mod_config_path)
            return mod_config_path
        else:
            return mod_template_path
    return mod_config_path


def get_user_config_path(config_path=None):
    if config_path is None:
        if os.path.exists(os.path.abspath(os.path.join(os.getcwd(), "config.yml"))):
            return os.path.abspath(os.path.join(os.getcwd(), "config.yml"))
        if os.path.exists(os.path.abspath(os.path.join(os.getcwd(), "config.json"))):
            return os.path.abspath(os.path.join(os.getcwd(), "config.json"))
        return None
    else:
        if not os.path.exists(config_path):
            system_log.error(_("config path: {config_path} does not exist.").format(config_path=config_path))
            return None
        return config_path


# def config_version_verify(config, config_path):
#     default_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../default_config.yml")
#     default_config = load_config(default_config_path, verify_version=False)
#     config_version = config.get("version", None)
#     if config_version != default_config["version"]:
#         back_config_file_path = config_path + "." + datetime.datetime.now().date().strftime("%Y%m%d") + ".bak"
#         shutil.move(config_path, back_config_file_path)
#         shutil.copy(default_config_path, config_path)
#
#         system_log.warning(_(u"""
# Your current config file {config_file_path} is too old and may cause RQAlpha running error.
# RQAlpha has replaced the config file with the newest one.
# the backup config file has been saved in {back_config_file_path}.
#         """).format(config_file_path=config_path, back_config_file_path=back_config_file_path))
#         config = default_config
#     return config


def set_locale(lc):
    # FIXME: It should depends on the system and locale config
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        locale.setlocale(locale.LC_CTYPE, "en_US.UTF-8")
        os.environ['TZ'] = 'Asia/Shanghai'
    except Exception as e:
        if os.name != 'nt':
            raise
    localization.set_locale([lc])


def parse_config(config_args, config_path=None, click_type=True, source_code=None):
    mod_configs = config_args.pop("mod_configs", [])
    for cfg, value in mod_configs:
        key = "mod__{}".format(cfg.replace(".", "__"))
        config_args[key] = mod_config_value_parse(value)

    set_locale(config_args.get("extra__locale", None))

    user_config_path = get_user_config_path(config_path)
    mod_config_path = get_mod_config_path()

    # load default config from rqalpha
    config = load_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../default_config.yml"))
    # load mod config
    mod_config = load_config(mod_config_path)
    deep_update(mod_config, config)
    # load user config
    user_config = load_config(user_config_path)
    deep_update(user_config, config)

    # use config_args to extend config
    if click_type:
        for key, value in six.iteritems(config_args):
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

    # config from user code
    config = parse_user_config_from_code(config, source_code)
    config = RqAttrDict(config)

    base_config = config.base
    extra_config = config.extra

    set_locale(extra_config.locale)

    if isinstance(base_config.start_date, six.string_types):
        base_config.start_date = datetime.datetime.strptime(base_config.start_date, "%Y-%m-%d")
    if isinstance(base_config.start_date, datetime.datetime):
        base_config.start_date = base_config.start_date.date()
    if isinstance(base_config.end_date, six.string_types):
        base_config.end_date = datetime.datetime.strptime(base_config.end_date, "%Y-%m-%d")
    if isinstance(base_config.end_date, datetime.datetime):
        base_config.end_date = base_config.end_date.date()

    if base_config.data_bundle_path is None:
        base_config.data_bundle_path = os.path.expanduser("~/.rqalpha")

    base_config.data_bundle_path = os.path.abspath(base_config.data_bundle_path)

    if os.path.basename(base_config.data_bundle_path) != "bundle":
        base_config.data_bundle_path = os.path.join(base_config.data_bundle_path, "./bundle")

    if not os.path.exists(base_config.data_bundle_path):
        system_log.error(
            _(u"data bundle not found in {bundle_path}. Run `rqalpha update_bundle` to download data bundle.").format(
                bundle_path=base_config.data_bundle_path))
        return

    if source_code is None and not os.path.exists(base_config.strategy_file):
        system_log.error(
            _(u"strategy file not found in {strategy_file}").format(strategy_file=base_config.strategy_file))
        return

    base_config.run_type = parse_run_type(base_config.run_type)
    base_config.account_list = parse_account_list(base_config.securities)
    base_config.persist_mode = parse_persist_mode(base_config.persist_mode)

    if extra_config.log_level.upper() != "NONE":
        user_log.handlers.append(user_std_handler)
        if not extra_config.user_system_log_disabled:
            user_system_log.handlers.append(user_std_handler)

    if extra_config.context_vars:
        if isinstance(extra_config.context_vars, six.string_types):
            extra_config.context_vars = json.loads(to_utf8(extra_config.context_vars))

    if base_config.stock_starting_cash < 0:
        raise patch_user_exc(ValueError(_(u"invalid stock starting cash: {}").format(base_config.stock_starting_cash)))

    if base_config.future_starting_cash < 0:
        raise patch_user_exc(ValueError(_(u"invalid future starting cash: {}").format(base_config.future_starting_cash)))

    if base_config.stock_starting_cash + base_config.future_starting_cash == 0:
        raise patch_user_exc(ValueError(_(u"stock starting cash and future starting cash can not be both 0.")))

    system_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    std_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    user_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)
    user_system_log.level = getattr(logbook, extra_config.log_level.upper(), logbook.NOTSET)

    if base_config.frequency == "1d":
        logger.DATETIME_FORMAT = "%Y-%m-%d"

    system_log.debug("\n" + pformat(config.convert_to_dict()))

    return config


def parse_user_config_from_code(config, source_code=None):
    try:
        if source_code is None:
            with codecs.open(config["base"]["strategy_file"], encoding="utf-8") as f:
                source_code = f.read()

        scope = {}

        code = compile(source_code, config["base"]["strategy_file"], 'exec')
        six.exec_(code, scope)

        __config__ = scope.get("__config__", {})

        for sub_key, sub_dict in six.iteritems(__config__):
            if sub_key not in config["whitelist"]:
                continue
            deep_update(sub_dict, config[sub_key])

    except Exception as e:
        system_log.error(_(u"in parse_user_config, exception: {e}").format(e=e))
    finally:
        return config


def parse_account_list(securities):
    if isinstance(securities, (tuple, list)):
        return [ACCOUNT_TYPE[security.upper()] for security in securities]
    elif isinstance(securities, six.string_types):
        return [ACCOUNT_TYPE[securities.upper()]]
    else:
        raise NotImplementedError


def parse_run_type(rt_str):
    assert isinstance(rt_str, six.string_types)
    if rt_str == "b":
        return RUN_TYPE.BACKTEST
    elif rt_str == "p":
        return RUN_TYPE.PAPER_TRADING
    elif rt_str == 'r':
        return RUN_TYPE.LIVE_TRADING
    else:
        raise NotImplementedError


def parse_persist_mode(persist_mode):
    assert isinstance(persist_mode, six.string_types)
    if persist_mode == 'real_time':
        return PERSIST_MODE.REAL_TIME
    elif persist_mode == 'on_crash':
        return PERSIST_MODE.ON_CRASH
    else:
        raise RuntimeError(_(u"unknown persist mode: {persist_mode}").format(persist_mode=persist_mode))
