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

import os
import collections
from copy import deepcopy
from importlib import import_module

import six


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.items():
        if (key in to_dict.keys() and
                isinstance(to_dict[key], collections.Mapping) and
                isinstance(value, collections.Mapping)):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value


def import_tests(dir, module):
    strategies = {}

    for file in os.listdir(dir):
        file_path = os.path.join(dir, file)
        if os.path.isdir(file_path):
            if not file.startswith("__"):
                strategies.update(import_tests(file_path, ".".join((module, file))))
        else:
            if file.endswith(".py") and file.startswith("test"):
                m = import_module(".".join((module, file[:-3])), "tests.api_tests")
                default_config = m.__dict__.pop("__config__", {})
                for obj in six.itervalues(m.__dict__):
                    if hasattr(obj, "__call__") and getattr(obj, "__name__", "").startswith("test"):
                        strategy_locals = obj()
                        custom_config = strategy_locals.pop("__config__", {})
                        config = deepcopy(default_config)
                        if custom_config:
                            deep_update(custom_config, config)
                        strategy_locals["config"] = config
                        strategy_locals["name"] = obj.__name__
                        strategies[".".join((module, file[:-3], obj.__name__))] = strategy_locals
    return strategies


strategies = list(six.itervalues(import_tests(os.path.dirname(__file__), "")))
