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

from rqalpha.apis import *
from rqalpha import run_func
from rqalpha.utils.dict_func import deep_update

__config__ = {
    "base": {
        "start_date": "2016-03-07",
        "end_date": "2016-03-08",
        "frequency": "1d",
        "accounts": {
            "stock": 1000000,
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        }
    },
}


def _config(c):
    config = deepcopy(__config__)
    deep_update(c, config)
    return config


def test_stock_sellable():
    def init(context):
        context.fired = False
        context.s = "000001.XSHE"

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 1000)
            sellable = context.portfolio.positions[context.s].sellable
            assert sellable == 0, "wrong sellable {}, supposed to be {}".format(sellable, 0)
            context.fired = True

    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_trading_pnl():

    config = _config({
        "base": {
            "start_date": "2020-01-02",
            "end_date": "2020-01-02",
            "frequency": "1d",
            "accounts": {
                "future": 1000000,
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            }
        },
    })

    def init(context):
        context.quantity = 2
        context.open_price = None
        context.close_price = None

    def open_auction(context, bar_dict):
        context.open_price = buy_open("IC2001", context.quantity).avg_price

    def handle_bar(context, bar_dict):
        context.close_price = sell_close("IC2001", context.quantity).avg_price

    def after_trading(context):
        pos = get_position("IC2001")
        # 当天交易盈亏 == (卖出价 - 买入价) * 数量 * 合约乘数
        assert pos.trading_pnl == (5361.8 - 5300.0) * context.quantity * 200
        assert pos.trading_pnl == (context.close_price - context.open_price) * context.quantity * 200

    run_func(config=config, init=init, open_auction=open_auction, handle_bar=handle_bar, after_trading=after_trading)

