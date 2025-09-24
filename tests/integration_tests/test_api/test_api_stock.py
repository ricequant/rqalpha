# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。


from copy import deepcopy
from rqalpha import run_func
from rqalpha.apis import *

__config__ = {
    "base": {
        "start_date": "2016-03-07",
        "end_date": "2016-03-08",
        "frequency": "1d",
        "accounts": {
            "stock": 100000000
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}


def test_order_shares(assert_order):
    config = deepcopy(__config__)
    config["base"].update({
        "start_date": "2016-06-14",
        "end_date": "2016-06-19",
    })

    # FIXME: supposed to check portfolio
    def init(context):
        context.counter = 0
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):

        context.counter += 1

        if context.counter == 1:
            order_price = bar_dict[context.s1].limit_up
            o = order_shares(context.s1, 1910, order_price)
            assert_order(o, order_book_id=context.s1, side=SIDE.BUY, quantity=1900, price=order_price)
        elif context.counter == 3:
            assert context.portfolio.positions[context.s1].quantity == 2280
            o = order_shares(context.s1, -1010, bar_dict[context.s1].limit_down)
            assert_order(o, side=SIDE.SELL, quantity=1000, status=ORDER_STATUS.FILLED)
        elif context.counter == 4:
            assert context.portfolio.positions[context.s1].quantity == 1280
            o = order_shares(context.s1, -1280, bar_dict[context.s1].limit_down)
            assert_order(o, quantity=1280, status=ORDER_STATUS.FILLED)
            assert context.portfolio.positions[context.s1].quantity == 0

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_order_lots(assert_order):
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        o = order_lots(context.s1, 1, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=100, price=order_price)
    
    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_order_value(assert_order):
    def init(context):
        context.s1 = "000001.XSHE"
        context.amount = 100

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        # 5 块最小手续费
        o = order_value(context.s1, context.amount * order_price + 5, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=context.amount, price=order_price)
    
    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_order_percent(assert_order):
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        o = order_percent(context.s1, 0.0001, bar_dict[context.s1].limit_up)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    
    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_order_target_value(assert_order):
    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.amount = 10000

    def handle_bar(context, bar_dict):
        o = order_target_percent(context.s1, 0.02, style=LimitOrder(bar_dict[context.s1].limit_up))
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    
    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_auto_switch_order_value():
    config = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-07",
            "accounts": {
                "stock": 2000
            }
        },
        "mod": {
            "sys_accounts": {
                "auto_switch_order_value": True
            },
        }
    }

    def handle_bar(context, _):
        order_shares("000001.XSHE", 200)
        assert context.portfolio.positions["000001.XSHE"].quantity == 100
    
    run_func(config=config, handle_bar=handle_bar)


def test_order_target_portfolio():
    config = {
        "base": {
            "start_date": "2019-07-30",
            "end_date": "2019-08-05",
            "accounts": {
                "stock": 1000000
            }
        },
    }

    def init(context):
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_target_portfolio({
                "000001.XSHE": 0.1,
                "000004.XSHE": 0.2,
            })
            # 开仓仓位在 rqalpha == 5.4.2 之后修改为四舍五入
            assert get_position("000001.XSHE").quantity == 7000   # (1000000 * 0.1) / 14.37 = 6958.94
            assert get_position("000004.XSHE").quantity == 10600  # (1000000 * 0.2) / 18.92 = 10570.82
        elif context.counter == 2:
            order_target_portfolio({
                "000004.XSHE": 0.1,
                "000005.XSHE": 0.2,
                "600519.XSHG": 0.6,
            }, {
                "000004.XSHE": (18.5, 18),
                "000005.XSHE": (2.92, ),
                "600519.XSHG": (970, 980),
            })
            assert get_position("000001.XSHE").quantity == 0  # 清仓
            assert get_position("000004.XSHE").quantity == 5500  # (993695.7496 * 0.1) / 18 = 5520.53
            assert get_position("000005.XSHE").quantity == 68000  # (993695.7496 * 0.2) / 2.92 = 68061.35
            assert get_position("600519.XSHG").quantity == 0  # 970 低于 收盘价 无法买进

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_order_target_portfolio_in_signal_mode():
    config = {
        "base": {
            "start_date": "2019-07-30",
            "end_date": "2019-08-05",
            "accounts": {
                "stock": 1000000
            }
        },
        "mod": {
            "sys_simulation": {
                "signal": True
            }
        }
    }

    def init(context):
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_target_portfolio({
                "000001.XSHE": 0.1,
                "000004.XSHE": 0.2,
            }, {
                "000001.XSHE": 14,
                "000004.XSHE": 10,
            })
            assert get_position("000001.XSHE").quantity == 7100   # (1000000 * 0.1) / 14.37 = 7142.86
            assert get_position("000004.XSHE").quantity == 0  # 价格低过跌停价，被拒单

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_is_st_stock():
    config = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-07",
        }
    }

    def handle_bar(_, __):
        for order_book_id, expected_result in [
            ("600603.XSHG", [True, True]),
            ("600305.XSHG", [False, False])
        ]:
            result = is_st_stock(order_book_id, 2)
            assert result == expected_result

    run_func(config=config, handle_bar=handle_bar)


def test_ksh():
    """科创版买卖最低200股，大于就可以201，202股买卖"""
    config = {
        "base": {
            "start_date": "2019-07-30",
            "end_date": "2019-08-05",
            "accounts": {
                "stock": 1000000
            }
        }
    }

    def init(context):
        context.counter = 0
        context.amount_s1 = 100
        context.amount_s2 = 200

        context.s1 = "688016.XSHG"
        context.s2 = "688010.XSHG"

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_shares(context.s1, 201)
            order_shares(context.s2, 199)

            assert context.portfolio.positions[context.s1].quantity == 201
            assert context.portfolio.positions[context.s2].quantity == 0
        if context.counter == 2:
            order_lots(context.s1, 2)

            order_price_s1 = bar_dict[context.s1].close
            order_price_s2 = bar_dict[context.s2].close
            # 5 块最小手续费
            order_value(context.s1, context.amount_s1 * order_price_s1 + 5, order_price_s1)
            order_value(context.s2, context.amount_s2 * order_price_s2 + 5, order_price_s2)
            assert context.portfolio.positions[context.s1].quantity == 201
            assert context.portfolio.positions[context.s2].quantity == 0

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_finance_repay():
    """ 测试融资还款接口 """

    financing_rate = 0.1
    money = 10000

    config = deepcopy(__config__)
    config["base"].update({
        "start_date": "2016-01-01",
        "end_date": "2016-01-31",
    })
    config["mod"].update({
        "sys_accounts": {
            "financing_rate": financing_rate,
        }
    })

    def cal_interest(capital, days):
        for i in range(days):
            capital += capital * financing_rate / 365
        return capital

    def init(context):
        context.fixed = True
        context.total = 0

    def handle_bar(context, bar_dict):
        if context.fixed:
            finance(money)
            context.fixed = False

        if context.total == 5:
            assert context.stock_account.cash_liabilities == cal_interest(money, 5)
        elif context.total == 10:
            assert context.stock_account.cash_liabilities == cal_interest(money, 10)
            repay(10100)
        elif context.total == 11:
            assert context.stock_account.total_value == 99999972.5689376
            assert context.stock_account.cash_liabilities == 0

        context.total += 1

    run_func(config=config, init=init, handle_bar=handle_bar)
