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

import copy
import typing
from collections import OrderedDict

from rqalpha.interface import AbstractMod
from rqalpha.utils.package_helper import import_mod
from rqalpha.utils.logger import system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils import RqAttrDict


class ModHandler(object):
    def __init__(self):
        self._env = None
        self._mod_list = list()  # type: typing.List[typing.Tuple[str, RqAttrDict]]
        self._mod_dict = OrderedDict()  # type: typing.OrderedDict[str, AbstractMod]

    def set_env(self, environment):
        self._env = environment

        config = environment.config

        for mod_name in config.mod.__dict__:
            mod_config = getattr(config.mod, mod_name)
            if not mod_config.enabled:
                continue
            self._mod_list.append((mod_name, mod_config))

        for idx, (mod_name, user_mod_config) in enumerate(self._mod_list):
            if hasattr(user_mod_config, 'lib'):
                lib_name = user_mod_config.lib
            elif mod_name in SYSTEM_MOD_LIST:
                lib_name = "rqalpha.mod.rqalpha_mod_" + mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            system_log.debug(_(u"loading mod {}").format(lib_name))
            mod_module = import_mod(lib_name)
            if mod_module is None:
                del self._mod_list[idx]
                return
            mod = mod_module.load_mod()  # type: AbstractMod

            mod_config = RqAttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))
            mod_config.update(user_mod_config)
            setattr(config.mod, mod_name, mod_config)
            self._mod_list[idx] = (mod_name, mod_config)
            self._mod_dict[mod_name] = mod

        self._mod_list.sort(key=lambda item: getattr(item[1], "priority", 100))
        environment.mod_dict = self._mod_dict

    def start_up(self):
        for mod_name, mod_config in self._mod_list:
            system_log.debug(_(u"mod start_up [START] {}\n{}").format(mod_name, mod_config))
            self._mod_dict[mod_name].start_up(self._env, mod_config)
            system_log.debug(_(u"mod start_up [END]   {}").format(mod_name))

    def tear_down(self, *args):
        result = {}
        for mod_name, __ in reversed(self._mod_list):
            try:
                system_log.debug(_(u"mod tear_down [START] {}").format(mod_name))
                ret = self._mod_dict[mod_name].tear_down(*args)
                system_log.debug(_(u"mod tear_down [END]   {}").format(mod_name))
            except Exception as e:
                system_log.exception("tear down fail for {}", mod_name)
                continue
            if ret is not None:
                result[mod_name] = ret
        return result


SYSTEM_MOD_LIST = [
    "sys_accounts",
    "sys_analyser",
    "sys_progress",
    "sys_risk",
    "sys_simulation",
    "sys_transaction_cost",
    'sys_scheduler',
]
