# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import click
from rqalpha import cli

__config__ = {
    # 股票最小手续费，单位元（即将废弃）
    "cn_stock_min_commission": None,
    # 股票最小手续费，单位元，默认 5
    "stock_min_commission": 5,
    # 股票佣金倍率,即在默认的手续费率基础上按该倍数进行调整，股票的默认佣金为万八
    "stock_commission_multiplier": 1,
    # 期货佣金倍率,即在默认的手续费率基础上按该倍数进行调整，期货默认佣金因合约而异
    "futures_commission_multiplier": 1,
    # 印花倍率，即在默认的印花税基础上按该倍数进行调整，股票默认印花税为千分之一，单边收取
    "tax_multiplier": 1,
    # 是否使用回测当时时间点对应的真实印花税率
    "pit_tax": False,
}

cli_prefix = "mod__sys_transaction_cost__"


cli.commands['run'].params.append(
    click.Option(
        ('-cm', '--commission-multiplier', cli_prefix + "commission_multiplier"),
        type=click.FLOAT,
        help="[sys_transaction_cost][deprecated] set commission multiplier"
    )
)


cli.commands['run'].params.append(
    click.Option(
        ('-scm', '--stock-commission-multiplier', cli_prefix + "stock_commission_multiplier"),
        type=click.FLOAT,
        help="[sys_transaction_cost] set stock commission multiplier"
    )
)


cli.commands['run'].params.append(
    click.Option(
        ('-fcm', '--futures-commission-multiplier', cli_prefix + "futures_commission_multiplier"),
        type=click.FLOAT,
        help="[sys_transaction_cost] set futures commission multiplier"
    )
)


cli.commands['run'].params.append(
    click.Option(
        ('-cnsmc', '--cn-stock-min-commission', cli_prefix + 'cn_stock_min_commission'),
        type=click.FLOAT,
        help="[sys_transaction_cost] set minimum commission in chinese stock trades."
    )
)

# [deprecated]
cli.commands['run'].params.append(
    click.Option(
        ('-smc', '--stock-min-commission', cli_prefix + 'cn_stock_min_commission'),
        type=click.FLOAT,
        help="[sys_transaction_cost][deprecated] set minimum commission in chinese stock trades."
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('-tm', '--tax-multiplier', cli_prefix + "tax_multiplier"),
        type=click.FLOAT,
        help="[sys_transaction_cost] set tax multiplier"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--pit-tax', cli_prefix + "pit_tax"),
        is_flag=True, default=False,
        help="[sys_transaction_cost] use historical tax"
    )
)


def load_mod():
    from .mod import TransactionCostMod
    return TransactionCostMod()
