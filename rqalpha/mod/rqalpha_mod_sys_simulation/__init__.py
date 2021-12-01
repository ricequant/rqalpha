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
    # 开启信号模式：该模式下，所有通过风控的订单将不进行撮合，直接产生交易
    "signal": False,
    # 撮合方式，其中：
    #   日回测的可选值为 "current_bar"|"vwap"（以当前 bar 收盘价｜成交量加权平均价撮合）
    #   分钟回测的可选值有 "current_bar"|"next_bar"|"vwap"（以当前 bar 收盘价｜下一个 bar 的开盘价｜成交量加权平均价撮合)
    #   tick 回测的可选值有 "last"|"best_own"|"best_counterparty"（以最新价｜己方最优价｜对手方最优价撮合）和 "counterparty_offer"（逐档撮合）
    "matching_type": "current_bar",
    # 开启对于处于涨跌停状态的证券的撮合限制
    "price_limit": True,
    # 开启对于对手盘无流动性的证券的撮合限制（仅在 tick 回测下生效）
    "liquidity_limit": False,
    # 开启成交量限制（仅在日和分钟回测下生效）
    #   开启该限制意味着每个 bar 的累计成交量将不会超过该时间段内市场上总成交量的一定比值（volume_percent）
    "volume_limit": True,
    # 每个 bar 可成交数量占市场总成交量的比值，在 volume_limit 开启时生效
    "volume_percent": 0.25,
    # 滑点模型，可选值有 "PriceRatioSlippage"（按价格比例设置滑点）和 "TickSizeSlippage"（按跳设置滑点）
    #    亦可自己实现滑点模型，选择自己实现的滑点模型时，此处需传入包含包和模块的完整类路径
    #    滑点模型类需继承自 rqalpha.mod.rqalpha_mod_sys_simulation.slippage.BaseSlippage
    "slippage_model": "PriceRatioSlippage",
    # 设置滑点值，对于 PriceRatioSlippage 表示价格的比例，对于 TickSizeSlippage 表示跳的数量
    "slippage": 0,
    # 开启对于当前 bar 无成交量的标的的撮合限制（仅在日和分钟回测下生效）
    "inactive_limit": True,
    # 账户每日计提的费用，需按照(账户类型，费率)的格式传入，例如[("STOCK", 0.0001), ("FUTURE", 0.0001)]
    "management_fee": [],
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
        type=click.Choice(
            ['current_bar', 'next_bar', 'last', 'best_own', 'best_counterparty', 'vwap', 'counterparty_offer']),
        help="[sys_simulation] set matching type"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--inactive-limit', cli_prefix + "inactive_limit"),
        type=click.BOOL,
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
