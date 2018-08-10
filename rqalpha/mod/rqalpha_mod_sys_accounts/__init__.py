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
    # 开启/关闭 股票 T+1， 默认开启
    "stock_t1": True,
    # 分红再投资
    "dividend_reinvestment": False,
    # 强平
    "future_forced_liquidation": True,
    # 当持仓股票退市时，按照退市价格返还现金
    "cash_return_by_stock_delisted": True
}


def load_mod():
    from .mod import AccountMod
    return AccountMod()


cli_prefix = "mod__sys_accounts__"

cli.commands['run'].params.append(
    click.Option(
        ('--stock-t1/--no-stock-t1', cli_prefix + "stock_t1"),
        default=None,
        help="[sys_accounts] enable/disable stock T+1"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--dividend-reinvestment', cli_prefix + 'dividend_reinvestment'),
        default=False, is_flag=True,
        help="[sys_accounts] enable dividend reinvestment"
    )
)


cli.commands['run'].params.append(
    click.Option(
        (
            '--cash-return-by-stock-delisted/--no-cash-return-by-stock-delisted',
            cli_prefix + 'cash_return_by_stock_delisted'
        ),
        default=True,
        help="[sys_simulation] return cash when stock delisted"
    )
)