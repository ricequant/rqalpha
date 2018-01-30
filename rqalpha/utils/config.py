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
import locale
import codecs

import pandas as pd
import yaml
import simplejson as json
import six

from rqalpha.const import RUN_TYPE, PERSIST_MODE
from rqalpha.utils import RqAttrDict, logger
from rqalpha.utils.i18n import gettext as _, localization
from rqalpha.utils.dict_func import deep_update
from rqalpha.utils.py2 import to_utf8
from rqalpha.utils.logger import system_log
from rqalpha.mod.utils import mod_config_value_parse


rqalpha_path = "~/.rqalpha"


def load_yaml(path):
    with codecs.open(path, encoding='utf-8') as f:
        return yaml.load(f)


def load_json(path):
    with codecs.open(path, encoding='utf-8') as f:
        return json.loads(f.read())


default_config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yml')
default_mod_config_path = os.path.join(os.path.dirname(__file__), '..', 'mod_config.yml')


def user_mod_conf_path():
    return os.path.join(os.path.expanduser(rqalpha_path), 'mod_config.yml')


def get_mod_conf():
    base = load_yaml(default_mod_config_path)
    user_mod_conf = os.path.join(os.path.expanduser(rqalpha_path), 'mod_config.yml')
    user = load_yaml(user_mod_conf) if os.path.exists(user_mod_conf) else {}
    deep_update(user, base)
    return base


def load_config_from_folder(folder):
    folder = os.path.expanduser(folder)
    path = os.path.join(folder, 'config.yml')
    base = load_yaml(path) if os.path.exists(path) else {}
    mod_path = os.path.join(folder, 'mod_config.yml')
    mod = load_yaml(mod_path) if os.path.exists(mod_path) else {}

    deep_update(mod, base)
    return base


def default_config():
    base = load_yaml(default_config_path)
    base['base']['source_code'] = None
    mod = load_yaml(default_mod_config_path)
    deep_update(mod, base)
    return base


def user_config():
    return load_config_from_folder(rqalpha_path)


def project_config():
    return load_config_from_folder(os.getcwd())


def code_config(config, source_code=None):
    try:
        if source_code is None:
            with codecs.open(config["base"]["strategy_file"], encoding="utf-8") as f:
                source_code = f.read()

        # FIXME: hardcode for parametric mod
        def noop(*args, **kwargs):
            pass
        scope = {'define_parameter': noop}

        code = compile(source_code, config["base"]["strategy_file"], 'exec')
        six.exec_(code, scope)

        return scope.get('__config__', {})
    except Exception as e:
        system_log.error(_(u"in parse_user_config, exception: {e}").format(e=e))
        return {}


def dump_config(config_path, config, dumper=yaml.Dumper):
    dirname = os.path.dirname(config_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with codecs.open(config_path, mode='w', encoding='utf-8') as stream:
        stream.write(to_utf8(yaml.dump(config, Dumper=dumper)))


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


def parse_config(config_args, config_path=None, click_type=False, source_code=None, user_funcs=None):
    conf = default_config()
    deep_update(user_config(), conf)
    deep_update(project_config(), conf)
    if config_path is not None:
        deep_update(load_yaml(config_path), conf)

    if 'base__strategy_file' in config_args and config_args['base__strategy_file']:
        # FIXME: ugly, we need this to get code
        conf['base']['strategy_file'] = config_args['base__strategy_file']
    elif ('base' in config_args and 'strategy_file' in config_args['base'] and
          config_args['base']['strategy_file']):
        conf['base']['strategy_file'] = config_args['base']['strategy_file']

    if user_funcs is None:
        for k, v in six.iteritems(code_config(conf, source_code)):
            if k in conf['whitelist']:
                deep_update(v, conf[k])

    mod_configs = config_args.pop('mod_configs', [])
    for k, v in mod_configs:
        key = 'mod__{}'.format(k.replace('.', '__'))
        config_args[key] = mod_config_value_parse(v)

    if click_type:
        for k, v in six.iteritems(config_args):
            if v is None:
                continue
            if k == 'base__accounts' and not v:
                continue

            key_path = k.split('__')
            sub_dict = conf
            for p in key_path[:-1]:
                if p not in sub_dict:
                    sub_dict[p] = {}
                sub_dict = sub_dict[p]
            sub_dict[key_path[-1]] = v
    else:
        deep_update(config_args, conf)

    config = RqAttrDict(conf)

    set_locale(config.extra.locale)

    def _to_date(v):
        return pd.Timestamp(v).date()

    config.base.start_date = _to_date(config.base.start_date)
    config.base.end_date = _to_date(config.base.end_date)

    if config.base.data_bundle_path is None:
        config.base.data_bundle_path = os.path.join(os.path.expanduser(rqalpha_path), "bundle")

    config.base.run_type = parse_run_type(config.base.run_type)
    config.base.accounts = parse_accounts(config.base.accounts)
    config.base.init_positions = parse_init_positions(config.base.init_positions)
    config.base.persist_mode = parse_persist_mode(config.base.persist_mode)

    if config.extra.context_vars:
        if isinstance(config.extra.context_vars, six.string_types):
            config.extra.context_vars = json.loads(to_utf8(config.extra.context_vars))

    if config.base.frequency == "1d":
        logger.DATETIME_FORMAT = "%Y-%m-%d"

    return config


def parse_accounts(accounts):
    a = {}
    if isinstance(accounts, tuple):
        accounts = {account_type: starting_cash for account_type, starting_cash in accounts}

    for account_type, starting_cash in six.iteritems(accounts):
        if starting_cash is None:
            continue
        starting_cash = float(starting_cash)
        a[account_type.upper()] = starting_cash
    if len(a) == 0:
        raise RuntimeError(_(u"None account type has been selected."))
    return a


def parse_init_positions(positions):
    # --position 000001.XSHE:1000,IF1701:-1
    result = []
    if not isinstance(positions, str):
        return result
    for s in positions.split(','):
        try:
            order_book_id, quantity = s.split(':')
        except ValueError:
            raise RuntimeError(_(u"invalid init position {}, should be in format 'order_book_id:quantity'").format(s))

        try:
            result.append((order_book_id, float(quantity)))
        except ValueError:
            raise RuntimeError(_(u"invalid quantity for instrument {order_book_id}: {quantity}").format(
                order_book_id=order_book_id, quantity=quantity))
    return result


def parse_run_type(rt_str):
    assert isinstance(rt_str, six.string_types)
    mapping = {
        "b": RUN_TYPE.BACKTEST,
        "p": RUN_TYPE.PAPER_TRADING,
        "r": RUN_TYPE.LIVE_TRADING,
    }
    try:
        return mapping[rt_str]
    except KeyError:
        raise RuntimeError(_(u"unknown run type: {}").format(rt_str))


def parse_persist_mode(persist_mode):
    assert isinstance(persist_mode, six.string_types)
    mapping = {
        "real_time": PERSIST_MODE.REAL_TIME,
        "on_crash": PERSIST_MODE.ON_CRASH,
        "on_normal_exit": PERSIST_MODE.ON_NORMAL_EXIT,
    }
    try:
        return mapping[persist_mode]
    except KeyError:
        raise RuntimeError(_(u"unknown persist mode: {}").format(persist_mode))
