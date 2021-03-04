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
    # 是否开启信号模式
    "signal": False,
    # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
    "matching_type": "current_bar",
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
    # volume 为 0 时限制成交
    "inactive_limit": True,
    # 账户级别每日的管理费用
    "management_fee": (),
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
        ('-mt', '--matching-type', cli_prefix + "matching_type"),
        type=click.Choice(['current_bar', 'next_bar', 'last', 'best_own', 'best_counterparty', 'vwap']),
        help="[sys_simulation] set matching type"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--inactive-limit', cli_prefix + "inactive_limit"),
        type=click.BOOL, default=True,
        help="[sys_simulation] Limit transaction when volume is 0"
    )
)

cli.commands["run"].params.append(
    click.Option(
        ('--management-fee', cli_prefix + "management_fee",),
        type=click.STRING, nargs=2, multiple=True,
        help="[sys_simulation] Account management rate. eg '--management-fee stock 0.0002' "
    )
)
