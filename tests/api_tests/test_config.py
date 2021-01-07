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

from rqalpha.environment import Environment

from ..utils import make_test_strategy_decorator

test_strategies = []

__config__ = {
    "base": {
        "start_date": "2018-04-01",
        "end_date": "2018-05-01",
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


def assert_almost_equal(first, second):
    assert round(abs(first - second), 10) == 0


def test_future_info():
    __config__ = {
        "base": {
            "future_info": {
                "SC": {
                    "close_commission_ratio": 0.0001,
                    "open_commission_ratio": 0.0002,
                    "commission_type": "BY_MONEY",
                }
            }
        }
        }

    def init(context):
        context.f1 = "SC1809"
        subscribe_event(EVENT.TRADE, on_trade)

    def handle_bar(*_):
        buy_open("SC1809", 2)
        sell_close("SC1809", 2, close_today=False)

    def on_trade(_, event):
        trade = event.trade
        contract_multiplier = Environment.get_instance().data_proxy.instruments("SC1809").contract_multiplier
        if trade.position_effect == POSITION_EFFECT.OPEN:
            assert_almost_equal(
                trade.transaction_cost, 0.0002 * trade.last_quantity * trade.last_price * contract_multiplier
            )
        elif trade.position_effect == POSITION_EFFECT.CLOSE:
            assert_almost_equal(
                trade.transaction_cost, 0.0001 * trade.last_quantity * trade.last_price * contract_multiplier
            )
        else:
            assert trade.transaction_cost == 0

    return locals()


def test_position():
    __config__ = {
        "base": {
            "accounts": {
                "stock": 10000000
            },
            "init_positions": "000006.XSHE:10000"
        },
   }

    def init(context):
        context.f1 = "000006.XSHE"
        stock_position = context.portfolio.get_position('000006.XSHE', 'LONG')
        assert stock_position.quantity == 10000

    return locals()
