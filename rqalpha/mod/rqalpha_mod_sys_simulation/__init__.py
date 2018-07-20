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

import click
from rqalpha import cli


__config__ = {
    # 是否开启信号模式
    "signal": False,
    # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
    "matching_type": "current_bar",
    # 股票最小手续费
    "stock_min_commission": 5,
    # 设置手续费乘数，默认为1
    "commission_multiplier": 1,
    # price_limit: 在处于涨跌停时，无法买进/卖出，默认开启【在 Signal 模式下，不再禁止买进/卖出，如果开启，则给出警告提示。】
    "price_limit": True,
    # liquidity_limit: 当对手盘没有流动性的时候，无法买进/卖出，默认关闭
    "liquidity_limit": False,
    # 是否有成交量限制
    "volume_limit": True,
    # 按照当前成交量的百分比进行撮合
    "volume_percent": 0.25,
    # 滑点模型，如果使用自己的定制的滑点，需要加上完整的包名
    "slippage_model": "PriceRatioSlippage",
    # 设置滑点
    "slippage": 0,
}


def load_mod():
    from .mod import SimulationMod
    return SimulationMod()


"""
注入 --signal option: 实现信号模式回测
注入 --slippage option: 实现设置滑点
注入 --commission-multiplier options: 实现设置手续费乘数
注入 --matching-type: 实现选择回测引擎
"""
cli_prefix = "mod__sys_simulation__"

cli.commands['run'].params.append(
    click.Option(
        ('--signal', cli_prefix + "signal"),
        is_flag=True, default=None,
        help="[sys_simulation] exclude match engine",
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('-sp', '--slippage', cli_prefix + "slippage"),
        type=click.FLOAT,
        help="[sys_simulation] set slippage"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--slippage-model', cli_prefix + "slippage_model"),
        type=click.STRING,
        help="[sys_simulation] set slippage model"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('-cm', '--commission-multiplier', cli_prefix + "commission_multiplier"),
        type=click.FLOAT,
        help="[sys_simulation] set commission multiplier"
    )
)

cli.commands['run'].params.append(
    # [Deprecated] using matching type
    click.Option(
        ('-me', '--match-engine', cli_prefix + "matching_type"),
        type=click.Choice(['current_bar', 'next_bar', 'last', 'best_own', 'best_counterparty']),
        help="[Deprecated][sys_simulation] set matching type"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('-mt', '--matching-type', cli_prefix + "matching_type"),
        type=click.Choice(['current_bar', 'next_bar', 'last', 'best_own', 'best_counterparty']),
        help="[sys_simulation] set matching type"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('-smc', '--stock-min-commission', cli_prefix + 'stock_min_commission'),
        type=click.FLOAT,
        help="[sys_simulation] set minimum commission in stock trades."
    )
)

