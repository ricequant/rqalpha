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

from datetime import date

from numpy.testing import assert_equal, assert_almost_equal
from rqalpha.apis import *


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


def test_stock_delist():
    import datetime

    __config__ = {
        "base": {
            "start_date": "2018-12-25",
            "end_date": "2019-01-05"
        }
    }

    def init(context):
        context.s = "000979.XSHE"
        context.fired = False
        context.total_value_before_delisted = None

    def handle_bar(context, _):
        if not context.fired:
            order_shares(context.s, 20000)
            context.fired = True
        if context.now.date() == datetime.date(2018, 12, 27):
            context.total_value_before_delisted = context.portfolio.total_value
        if context.now.date() > datetime.date(2018, 12, 28):
            assert context.portfolio.total_value == context.total_value_before_delisted
    return locals()


def test_stock_dividend():
    __config__ = {
        "base": {
            "start_date": "2012-06-04",
            "end_date": "2018-07-9"
        },
        "extra": {
            "log_level": "info"
        }
    }

    def init(context):
        context.s = "601088.XSHG"
        context.last_cash = None

    def handle_bar(context, _):
        if context.now.date() in (date(2012, 6, 8), date(2017, 7, 7), date(2018, 7, 6)):
            context.last_cash = context.portfolio.cash

        elif context.now.date() == date(2012, 6, 4):
            order_shares(context.s, 1000)
        elif context.now.date() == date(2012, 6, 18):
            assert context.portfolio.cash == context.last_cash + 900
        elif context.now.date() == date(2017, 7, 11):
            assert context.portfolio.cash == context.last_cash + 2970
        elif context.now.date() == date(2018, 7, 9):
            assert context.portfolio.cash == context.last_cash + 910

    return locals()


def test_stock_transform():
    __config__ = {
        "base": {
            "start_date": "2015-05-06",
            "end_date": "2015-05-20"
        }
    }

    def init(context):
        context.s1 = "601299.XSHG"
        context.s2 = "601766.XSHG"
        context.cash_before_transform = None

    def handle_bar(context, _):
        if context.now.date() == date(2015, 5, 6):
            order_shares(context.s1, 200)
            context.cash_before_transform = context.portfolio.cash
        elif context.now.date() >= date(2015, 5, 20):
            assert int(context.portfolio.positions[context.s2].quantity) == 220
            assert context.portfolio.cash == context.cash_before_transform

    return locals()


def test_stock_split():
    __config__ = {
        "base": {
            "start_date": "2016-05-26",
            "end_date": "2016-05-27"
        }
    }

    def init(context):
        context.s = "000035.XSHE"
        context.counter = 0
        context.cash_before_split = None

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_shares(context.s, 1000)
            assert_equal(get_position(context.s, POSITION_DIRECTION.LONG).quantity, 1000)
            context.cash_before_split = context.portfolio.cash
        elif context.counter == 2:
            position = get_position(context.s, POSITION_DIRECTION.LONG)
            assert_equal(position.quantity, 2000)
            assert_equal(position.trading_pnl, 0)
            assert_almost_equal(position.position_pnl, -140)
            assert_equal(context.portfolio.cash, context.cash_before_split)

    return locals()
