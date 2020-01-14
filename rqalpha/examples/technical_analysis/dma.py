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

# Run `rqalpha mod enable sys_funcat` first.
from rqalpha.api import *


def init(context):
    context.s1 = "600275.XSHG"


def handle_bar(context, bar_dict):
    S(context.s1)
    # 自己实现 DMA指标（Different of Moving Average）
    M1 = 5
    M2 = 89
    M3 = 36

    DDD = MA(CLOSE, M1) - MA(CLOSE, M2)
    AMA = MA(DDD, M3)

    plot("DDD", DDD.value)
    plot("AMA", AMA.value)

    cur_position = context.portfolio.positions[context.s1].quantity

    if DDD < AMA and cur_position > 0:
        order_target_percent(context.s1, 0)

    if (HHV(MAX(O, C), 50) / LLV(MIN(O, C), 50) < 2
        and CROSS(DDD, AMA) and cur_position == 0):
        order_target_percent(context.s1, 1)
