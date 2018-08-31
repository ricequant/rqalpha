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
    # A股最小手续费
    "cn_stock_min_commission": 5,
    # 港股最小手续费
    "hk_stock_min_commission": 50,
    # 设置手续费乘数，默认为1
    "commission_multiplier": 1,
}

cli_prefix = "mod__sys_transaction_cost__"


cli.commands['run'].params.append(
    click.Option(
        ('-cm', '--commission-multiplier', cli_prefix + "commission_multiplier"),
        type=click.FLOAT,
        help="[sys_simulation] set commission multiplier"
    )
)


cli.commands['run'].params.append(
    click.Option(
        ('-cnsmc', '--cn-stock-min-commission', cli_prefix + 'cn_stock_min_commission'),
        type=click.FLOAT,
        help="[sys_simulation] set minimum commission in chinese stock trades."
    )
)


cli.commands['run'].params.append(
    click.Option(
        ('-hksmc', '--hk-stock-min-commission', cli_prefix + 'hk_stock_min_commission'),
        type=click.FLOAT,
        help="[sys_simulation] set minimum commission in Hong Kong stock trades."
    )
)


# [deprecated]
cli.commands['run'].params.append(
    click.Option(
        ('-smc', '--stock-min-commission', cli_prefix + 'cn_stock_min_commission'),
        type=click.FLOAT,
        help="[sys_simulation][deprecated] set minimum commission in chinese stock trades."
    )
)


def load_mod():
    from .mod import TransactionCostMod
    return TransactionCostMod()
