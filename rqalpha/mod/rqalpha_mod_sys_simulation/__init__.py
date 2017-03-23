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

from .mod import SimulationMod


def load_mod():
    return SimulationMod()


__config__ = {
    # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
    "matching_type": "current_bar",
    # 设置滑点
    "slippage": 0,
    # 设置手续费乘数，默认为1
    "commission_multiplier": 1,
    # bar_limit: 在处于涨跌停时，无法买进/卖出，默认开启
    "bar_limit": True,
    # 按照当前成交量的百分比进行撮合
    "volume_percent": 0.25,
}
