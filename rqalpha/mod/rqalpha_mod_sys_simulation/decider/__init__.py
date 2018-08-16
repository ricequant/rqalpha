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

import importlib


from rqalpha.utils.i18n import gettext as _
from rqalpha.mod.rqalpha_mod_sys_simulation.decider.slippage import PriceRatioSlippage


class SlippageDecider(object):
    def __init__(self, module_name, rate):
        try:
            if "." not in module_name:
                module = importlib.import_module("rqalpha.mod.rqalpha_mod_sys_simulation.decider.slippage")
                slippage_cls = getattr(module, module_name)
            else:
                paths = module_name.split(".")
                module_paths, cls_name = paths[:-1], paths[-1]
                module = importlib.import_module(".".join(module_paths))
                slippage_cls = getattr(module, cls_name)
        except (ImportError, AttributeError):
            raise RuntimeError(_("Missing SlippageModel {}").format(module_name))

        self.decider = slippage_cls(rate)

    def get_trade_price(self, side, price):
        return self.decider.get_trade_price(side, price)
