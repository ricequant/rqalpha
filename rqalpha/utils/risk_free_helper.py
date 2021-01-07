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

YIELD_CURVE_TENORS = {
    0: '0S',
    30: '1M',
    60: '2M',
    90: '3M',
    180: '6M',
    270: '9M',
    365: '1Y',
    365 * 2: '2Y',
    365 * 3: '3Y',
    365 * 4: '4Y',
    365 * 5: '5Y',
    365 * 6: '6Y',
    365 * 7: '7Y',
    365 * 8: '8Y',
    365 * 9: '9Y',
    365 * 10: '10Y',
    365 * 15: '15Y',
    365 * 20: '20Y',
    365 * 30: '30Y',
    365 * 40: '40Y',
    365 * 50: '50Y',
}

YIELD_CURVE_DURATION = sorted(YIELD_CURVE_TENORS.keys())


def get_tenor_for(start_date, end_date):
    duration = (end_date - start_date).days
    tenor = 0
    for t in YIELD_CURVE_DURATION:
        if duration >= t:
            tenor = t
        else:
            break

    return YIELD_CURVE_TENORS[tenor]
