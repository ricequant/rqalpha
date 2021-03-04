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


__config__ = {
    "base": {
        "start_date": "2015-04-11",
        "end_date": "2015-04-20",
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
        },
        "sys_simulation": {
            "volume_limit": True,
            "volume_percent": 0.000002
        }
    },
}


def test_open_auction_match():
    __config__ = {
        "mod": {
            "sys_simulation": {
                "volume_limit": True,
                "volume_percent": 0.000002
            }
        },
    }

    def init(context):
        context.s = "000001.XSHE"
        context.bar = None
        context.first_day = True

    def open_auction(context, bar_dict):
        bar = bar_dict[context.s]
        if context.first_day:
            order_shares(context.s, 1000, bar.limit_up * 0.99)
            # 部分成交，仅能成交 900 股
            assert get_position(context.s).quantity == 900
            assert get_position(context.s).avg_price == bar.open

    def handle_bar(context, bar_dict):
        if context.first_day:
            bar = bar_dict[context.s]
            assert get_position(context.s).quantity == 1000
            assert get_position(context.s).avg_price == (bar.open * 900 + bar.close * 100) / 1000
            context.first_day = False

    return locals()


def test_vwap_match():
    __config__ = {
        "mod": {
            "sys_simulation": {
                "volume_limit": True,
                "matching_type": "vwap"
            }
        },
    }

    def init(context):
        context.s = "000001.XSHE"
        context.first_day = True
        context.vwap_price = None

    def handle_bar(context, bar_dict):
        if context.first_day == 1:
            bar = bar_dict[context.s]
            vwap_order = order_shares(context.s, 1000)
            assert bar.total_turnover / bar.volume == vwap_order.avg_price
            context.first_day = False

    return locals()
