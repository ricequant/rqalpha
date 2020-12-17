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
    # 开启/关闭 股票 T+1， 默认开启
    "stock_t1": True,
    # 分红再投资
    "dividend_reinvestment": False,
    # 当持仓股票退市时，按照退市价格返还现金
    "cash_return_by_stock_delisted": True,
    # 股票下单因资金不足被拒时改为使用全部剩余资金下单
    "auto_switch_order_value": False,
    # 检查股票可平仓位是否充足
    "validate_stock_position": True,
    # 检查期货可平仓位是否充足
    "validate_future_position": True,
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
        default=None, is_flag=True,
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


cli.commands['run'].params.append(
    click.Option(
        ("--no-short-stock/--short-stock", cli_prefix + "validate_stock_position"),
        is_flag=True, default=True,
        help="[sys_simulation] enable stock shorting"
    )
)
