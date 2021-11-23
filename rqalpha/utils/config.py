# -*- coding: utf-8 -*-
# 版权所有 2021 深圳米筐科技有限公司（下称“米筐科技”）
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

import os
import codecs

import pandas as pd
import yaml
import simplejson as json
import six

from rqalpha.const import RUN_TYPE, PERSIST_MODE, COMMISSION_TYPE
from rqalpha.utils import RqAttrDict, logger
from rqalpha.utils.i18n import gettext as _, set_locale
from rqalpha.utils.dict_func import deep_update
from rqalpha.utils.logger import system_log
from rqalpha.mod.utils import mod_config_value_parse


rqalpha_path = "~/.rqalpha"


def load_yaml(path):
    with codecs.open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


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
        stream.write(yaml.dump(config, Dumper=dumper))


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
        for k, v in code_config(conf, source_code).items():
            if k in conf['whitelist']:
                deep_update(v, conf[k])

    mod_configs = config_args.pop('mod_configs', [])
    for k, v in mod_configs:
        key = 'mod__{}'.format(k.replace('.', '__'))
        config_args[key] = mod_config_value_parse(v)

    if click_type:
        for k, v in config_args.items():
            # click multiple=True时传入tuple类型 无输入时为tuple()
            if v is None or (v == tuple()):
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
    config.base.future_info = parse_future_info(config.base.future_info)

    if config.extra.context_vars:
        if isinstance(config.extra.context_vars, six.string_types):
            config.extra.context_vars = json.loads(config.extra.context_vars)

    if config.base.frequency == "1d":
        logger.DATETIME_FORMAT = "%Y-%m-%d"

    return config


def parse_future_info(future_info):
    new_info = {}

    for underlying_symbol, info in future_info.items():
        try:
            underlying_symbol = underlying_symbol.upper()
        except AttributeError:
            raise RuntimeError(_("Invalid future info: underlying_symbol {} is illegal.".format(underlying_symbol)))

        for field, value in info.items():
            if field in (
                "open_commission_ratio", "close_commission_ratio", "close_commission_today_ratio"
            ):
                new_info.setdefault(underlying_symbol, {})[field] = float(value)
            elif field == "commission_type":
                if isinstance(value, six.string_types) and value.upper() == "BY_MONEY":
                    new_info.setdefault(underlying_symbol, {})[field] = COMMISSION_TYPE.BY_MONEY
                elif isinstance(value, six.string_types) and value.upper() == "BY_VOLUME":
                    new_info.setdefault(underlying_symbol, {})[field] = COMMISSION_TYPE.BY_VOLUME
                elif isinstance(value, COMMISSION_TYPE):
                    new_info.setdefault(underlying_symbol, {})[field] = value
                else:
                    raise RuntimeError(_(
                        "Invalid future info: commission_type is suppose to be BY_MONEY or BY_VOLUME"
                    ))
            else:
                raise RuntimeError(_("Invalid future info: field {} is not valid".format(field)))
    return new_info


def parse_accounts(accounts):
    a = {}
    if isinstance(accounts, tuple):
        accounts = {account_type: starting_cash for account_type, starting_cash in accounts}

    for account_type, starting_cash in accounts.items():
        if starting_cash is None:
            continue
        starting_cash = float(starting_cash)
        a[account_type.upper()] = starting_cash

    # if len(a) == 0:
    #     raise RuntimeError(_(u"None account type has been selected."))

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
