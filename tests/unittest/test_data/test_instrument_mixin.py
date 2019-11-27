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

from rqalpha.utils.testing import DataProxyFixture, RQAlphaTestCase


class InstrumentMixinTestCase(DataProxyFixture, RQAlphaTestCase):
    def init_fixture(self):
        super(InstrumentMixinTestCase, self).init_fixture()

    def test_get_trading_period(self):
        from datetime import time
        from rqalpha.utils import TimeRange

        rb_time_range = self.data_proxy.get_trading_period(["RB1912"])
        self.assertSetEqual(set(rb_time_range), {
            TimeRange(start=time(21, 1), end=time(23, 0)), TimeRange(start=time(9, 1), end=time(10, 15)),
            TimeRange(start=time(10, 31), end=time(11, 30)), TimeRange(start=time(13, 31), end=time(15, 0))
        })

        merged_time_range = self.data_proxy.get_trading_period(["AG1912", "TF1912"], [
            TimeRange(start=time(9, 31), end=time(11, 30)),
            TimeRange(start=time(13, 1), end=time(15, 0)),
        ])
        self.assertSetEqual(set(merged_time_range), {
            TimeRange(start=time(21, 1), end=time(23, 59)),
            TimeRange(start=time(0, 0), end=time(2, 30)),
            TimeRange(start=time(9, 1), end=time(11, 30)),
            TimeRange(start=time(13, 1), end=time(15, 15)),
        })

    def test_is_night_trading(self):
        assert not self.data_proxy.is_night_trading(["TF1912"])
        assert self.data_proxy.is_night_trading(["AG1912", "000001.XSHE"])
