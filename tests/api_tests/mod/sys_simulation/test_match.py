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
import os

from rqalpha.const import ORDER_STATUS

__config__ = {
    "base": {
        "frequency": "1d",
        "accounts": {
            "future": 1000000,
        }
    }
}


def test_match():

    try:
        import rqalpha_mod_ricequant_data
    except Exception:
        print("github上无数据，跳过测试，仅在本地测试")
        return {}

    __config__ = {
        "base": {
            "data_bundle_path": os.path.expanduser("~/.rqalpha-plus/bundle"),
            "start_date": "2023-07-07",
            "end_date": "2023-07-10",
            "frequency": "1m",
            "accounts": {
                "future": 1000000,
            }
        },
        "mod": {
            "ricequant_data": {
                "enabled": True
            }
        }
    }

    def init(context):
        context.order = None
        subscribe("ZN2309")
        subscribe("RR2309")

    def handle_bar(context, bar_dict):
        dt_str = context.now.strftime("%Y%m%d%H%M%S")
        # 当天夜盘
        if dt_str == "20230706210100":
            context.order = buy_open("RR2309", 1, price_or_style=3500)
        elif dt_str == "20230706230200":
            assert context.order.status == ORDER_STATUS.ACTIVE, "盘中休息也保持active"
            assert "订单被拒单: [RR2309] 当前缺失市场数据。" != context.order._message, "不能在非交易时段尝试撮合"
        # 第二天早盘
        elif dt_str == "20230707091000":
            assert context.order.status == ORDER_STATUS.ACTIVE, "夜盘下的order在未成交、撤单等情况下应保持active状态"
        # 第二天夜盘
        elif dt_str == "20230707210100":
            assert context.order.status == ORDER_STATUS.REJECTED, "上个交易日的订单在当天收盘后未被拒单"

    return locals()
