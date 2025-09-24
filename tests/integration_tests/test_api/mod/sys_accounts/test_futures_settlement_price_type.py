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

from copy import deepcopy
from datetime import date

from rqalpha.apis import *
from rqalpha import run_func
from rqalpha.utils.dict_func import deep_update

__config__ = {
    "base": {
        "start_date": "2016-01-01",
        "end_date": "2016-01-31",
        "frequency": "1d",
        "accounts": {
            "future": 1000000,
        }
    },
    "mod": {
        "sys_accounts": {
            "futures_settlement_price_type": "settlement"
        }
    }
}


def _config(c):
    config = deepcopy(__config__)
    deep_update(c, config)
    return config


def test_futures_settlement_price_type():

    def init(context):
        context.fixed = True
        context.symbol = "IC1603"
        context.total = 0

    def handle_bar(context, bar_dict):
        if context.fixed:
            buy_open(context.symbol, 1)
            context.fixed = False
        context.total += 1

    def after_trading(context):
        pos = get_position(context.symbol)
        # close - prev_settlement
        if context.total == 2:
            assert pos.position_pnl == (6364.6 - 6657.0) * 200
        elif context.total == 3:
            assert pos.position_pnl == (6468 - 6351.2) * 200
    
    run_func(config=__config__, init=init, handle_bar=handle_bar, after_trading=after_trading)


def test_futures_de_listed():
    """ 期货合约到期交割 """

    config = _config({
        "base": {
            "start_date": "2016-03-17",
            "end_date": "2016-03-21",
            "frequency": "1d",
            "accounts": {
                "future": 1000000,
            }
        },
        "mod": {
            "sys_transaction_cost": {
                # 期货佣金倍率,即在默认的手续费率基础上按该倍数进行调整，期货默认佣金因合约而异
                "futures_commission_multiplier": 0,
            },
            "sys_accounts": {
                "futures_settlement_price_type": "settlement"
            }
        }
    })

    def init(context):
        pass

    def before_trading(context):
        if context.now.date() == date(2016, 3, 21):
            assert context.portfolio.total_value == context.total_value + (5944.29 - 5760.0) * 200, "合约交割后的总权益有误"

    def handle_bar(context, bar_dict):
        if context.now.date() == date(2016, 3, 17):
            buy_open("IC1603", 1)
            context.total_value = context.portfolio.total_value

    run_func(config=config, init=init, before_trading=before_trading, handle_bar=handle_bar)
