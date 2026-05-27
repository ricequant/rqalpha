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
from math import isclose

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


def test_dividend_reinvestment_and_splits_on_the_same_day():
    """
    测试分红再投资和拆股行为在同一天时的逻辑，只要测试点为：在当日分红再投资买入的票不应当参与拆股
    """
    config = _config({
        "base": {
            "start_date": "2017-02-01",
            "end_date": "2017-03-10",
            "frequency": "1d",
            "accounts": {
                "stock": 10000000
            },
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_accounts": {
                "dividend_reinvestment": True
            }
        }
    })

    def init(context):
        context.s1 = "600816.XSHG"
        context.fired = False

    def handle_bar(context, bar_dict):
        if not context.fired:
            order_shares(context.s1, 10000)
            context.fired = True
            assert get_position(context.s1).quantity == 10000
        if context.now.date() == date(2017, 3, 6):
            # 1. 每 1 股拆为 2.2 股
            # 2. 每 10 股分现金 6 元，总共分 6000 元，再投资买入 400 股
            assert get_position(context.s1).quantity == 22400

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_dividend_reinvestment_with_transaction():
    """
    测试分红再投资时考虑手续费
    """
    config = _config({
        "base": {
            "start_date": "2013-06-10",
            "end_date": "2013-06-21",
            "accounts": {
                "stock": 10000,
            },
            "init_positions": "000001.XSHE:15000",
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_accounts": {
                "dividend_reinvestment": True
            }
        }
    })

    def init(context):
        context.s1 = "000001.XSHE"
        context.fired = False

    def handle_bar(context, bar_dict):
        if not context.fired:
            assert get_position(context.s1).quantity == 15000
            context.fired = True
        if context.now.date() == date(2013, 6, 20):
            # 1. 每 1 股拆为 1.6 股
            # 2. 每 10 股分现金 1.7 元，总共分 2550 元，再投资买入 200 股
            assert get_position(context.s1).quantity == 24200
            # 分红再投资的剩余现金为 2550 - (200 * 11.9187 + 5)
            assert context.stock_account.cash - 10000 == 161.25
            
    
    run_func(config=config, init=init, handle_bar=handle_bar)


def test_dividend_tax():
    """
    测试红利税
    """
    config = {
        "base": {
            "start_date": "2024-9-20",
            "end_date": "2025-12-31",
            "accounts": {
                "stock": 100000,
            }
        },
        "mod": {
            "sys_accounts": {
                "dividend_tax_enabled": True
            }
        }
    }


    def init(context):
        context.s1 = "000001.XSHE"
        context.s2 = "600000.XSHG"
        context.fired = False
        
    def handle_bar(context, bar_dict):
        today = context.now.date()
        if not context.fired:
            order_shares(context.s1, 1000)
            order_shares(context.s2, 1000)
            context.fired = True
        if today == date(2024, 10, 10):
            # 20241010: 000001.XSHE 分红到账，每股分红 0.246 元，不进行扣税
            assert isclose(context.stock_account.cash, context.cash + 0.246 * 1000)
        elif today == date(2024, 10, 11):
            # 持仓期限小于等于一个月，卖出票时应按 20% 税率收取红利税
            order = order_shares(context.s1, -500)
            assert isclose(context.stock_account.cash, context.cash + order.avg_price * 500 - order.transaction_cost - 0.246 * 500 * 0.2)
        elif today == date(2025, 5, 20):
            # 买入一批新的 000001.XSHE 仓位，买入后仓位组成为: {20240920: 500, 20250520: 500}
            order_shares(context.s1, 500)
        elif today == date(2025, 6, 12):
            # 20250612: 000001.XSHE 分红到账，每股 0.362 元，不进行扣税
            assert isclose(context.stock_account.cash, context.cash + 0.362 * 1000)
        elif today == date(2025, 6, 13):
            # 卖出 700 股，结果应该 500 股 20240920 的仓位 + 200 股 20250520 的仓位
            order = order_shares(context.s1, -700)
            dividend_tax_1 = (0.246 + 0.362) * 500 * 0.1  # 20240920 买入的仓位，税率为 10%
            dividend_tax_2 = 0.362 * 200 * 0.2  # 20250520 买入的仓位，税率为 20%
            assert isclose(context.stock_account.cash, context.cash + order.avg_price * 700 - order.transaction_cost - dividend_tax_1 - dividend_tax_2)
        elif today == date(2025, 7, 16):
            # 20250716: 600000.XSHG 分红到账，每股分红 0.41 元，不进行扣税
            assert isclose(context.stock_account.cash, context.cash + 0.41 * 1000)
        elif today == date(2025, 12, 30):
            # 卖出全部的 600000.XSHG 仓位，持仓期限已经超过 1 年，不需要征收红利税
            order = order_shares(context.s2, -1000)
            assert isclose(context.stock_account.cash, context.cash + order.avg_price * 1000 - order.transaction_cost)

        context.cash = context.stock_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)