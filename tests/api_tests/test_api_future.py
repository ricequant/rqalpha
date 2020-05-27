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


from ..utils import assert_order

__config__ = {
    "base": {
        "start_date": "2016-03-07",
        "end_date": "2016-03-08",
        "frequency": "1d",
        "accounts": {
            "future": 10000000000
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


def test_buy_open():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        o = buy_open(context.f1, 1)
        assert_order(
            o, order_book_id=context.f1, quantity=1, status=ORDER_STATUS.FILLED, side=SIDE.BUY, position_effect=POSITION_EFFECT.OPEN
        )
    return locals()


def test_sell_open():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        o = sell_open(context.f1, 1)
        assert_order(
            o, order_book_id=context.f1, quantity=1, status=ORDER_STATUS.FILLED, side=SIDE.SELL, position_effect=POSITION_EFFECT.OPEN
        )
    return locals()


def test_buy_close():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        orders = buy_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0
    return locals()


def test_sell_close():
    def init(context):
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        orders = sell_close(context.f1, 1)
        # TODO: Add More Sell Close Test
        assert len(orders) == 0
    return locals()


def test_close_today():
    def init(context):
        context.fired = False
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        if not context.fired:
            buy_open(context.f1, 2)
            sell_close(context.f1, 1, close_today=True)
            assert get_position(context.f1).quantity == 1
            context.fired = True

    return locals()


def test_future_order_to():
    def init(context):
        context.counter = 0
        context.f1 = 'P88'
        subscribe(context.f1)

    def handle_bar(context, _):
        context.counter += 1
        if context.counter == 1:
            order_to(context.f1, 3)
            assert get_position(context.f1).quantity == 3
            order_to(context.f1, 2)
            assert get_position(context.f1).quantity == 2
        elif context.counter == 2:
            order_to(context.f1, -2)
            assert get_position(context.f1, POSITION_DIRECTION.SHORT).quantity == 2
            order_to(context.f1, 1)
            assert get_position(context.f1, POSITION_DIRECTION.SHORT).quantity == 0
            assert get_position(context.f1, POSITION_DIRECTION.LONG).quantity == 1

    return locals()
