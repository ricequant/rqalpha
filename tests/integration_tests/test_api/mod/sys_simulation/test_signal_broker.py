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

from rqalpha.apis import *
from rqalpha import run_func
from rqalpha.environment import Environment
from rqalpha.utils.dict_func import deep_update

__config__ = {
    "base": {
        "start_date": "2015-04-10",
        "end_date": "2015-04-10",
        "frequency": "1d",
        "accounts": {
            "stock": 1000000,
            "future": 1000000
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
        "sys_simulation": {
            "signal": True,
        }
    },
}


def _config(c):
    config = deepcopy(__config__)
    deep_update(c, config)
    return config


def test_price_limit():
    def handle_bar(context, bar_dict):
        stock = "000001.XSHE"
        tick_size = Environment.get_instance().data_proxy.get_tick_size(stock)
        price = bar_dict[stock].limit_up * 0.99
        order_shares(stock, 100, price)
        assert get_position(stock).quantity == 100
        assert get_position(stock).avg_price == price

        # 进入涨停前最后一个 tick 区间的未 round 价格也应拒单
        order_shares(stock, 100, bar_dict[stock].limit_up - tick_size + 5e-6)
        assert get_position(stock).quantity == 100
        assert get_position(stock).avg_price == price

        # 进入跌停前最后一个 tick 区间的未 round 价格也应拒单
        order_shares(stock, -100, bar_dict[stock].limit_down + tick_size - 5e-6)
        assert get_position(stock).quantity == 100
        assert get_position(stock).avg_price == price

    run_func(config=__config__, handle_bar=handle_bar)


def test_price_limit_sell_open():
    def init(context):
        context.future = "P88"
        subscribe(context.future)

    def handle_bar(context, bar_dict):
        tick_size = Environment.get_instance().data_proxy.get_tick_size(context.future)
        valid_price = bar_dict[context.future].limit_down + tick_size
        sell_open(context.future, 1, valid_price)
        assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 1
        assert get_position(context.future, POSITION_DIRECTION.SHORT).avg_price == valid_price

        sell_open(context.future, 1, bar_dict[context.future].limit_down + tick_size - 5e-6)
        assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 1
        assert get_position(context.future, POSITION_DIRECTION.SHORT).avg_price == valid_price

    run_func(config=__config__, init=init, handle_bar=handle_bar)


def test_signal_open_auction():

    def init(context):
        context.fixed = True

    def open_auction(context, bar_dict):
        if context.fixed:
            order_shares("000001.XSHE", 1000)
            buy_open("AU1512", 1)
            pos = get_position("000001.XSHE")
            assert pos.quantity == 1000
            assert pos.avg_price == 18.0
            pos = get_position("AU1512")
            assert pos.quantity == 1
            assert pos.avg_price == 242.2
            context.fixed = False

    run_func(config=__config__, init=init, open_auction=open_auction)
