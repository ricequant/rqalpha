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

import os
import pickle
from datetime import datetime

from rqalpha.utils.testing import RQAlphaTestCase, DataProxyFixture, UniverseFixture
from rqalpha.mod.rqalpha_mod_sys_simulation.testing import SimulationEventSourceFixture


class SimulationEventSourceTestCase(UniverseFixture, SimulationEventSourceFixture, DataProxyFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(SimulationEventSourceTestCase, self).__init__(*args, **kwargs)
        self._ticks = None

    def init_fixture(self):
        super(SimulationEventSourceTestCase, self).init_fixture()
        self._ticks = pickle.loads(open(
            os.path.join(os.path.dirname(__file__), "mock_data/mock_ticks.pkl"), "rb"
        ).read())

    def _mock_get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        for tick in self._ticks:
            if tick.order_book_id not in order_book_id_list:
                continue
            if self.env.data_proxy.get_future_trading_date(tick.datetime).date() != trading_date.date():
                continue
            if last_dt and tick.datetime <= last_dt:
                continue
            yield tick

    def assertEvent(self, e, event_type, calendar_dt, trading_dt, **kwargs):
        kwargs.update({
            "event_type": event_type,
            "calendar_dt": calendar_dt,
            "trading_dt": trading_dt
        })
        self.assertObj(e, **kwargs)

    def test_tick_events(self):
        from rqalpha.core.events import EVENT

        with self.mock_data_proxy_method("get_merge_ticks", self._mock_get_merge_ticks):
            events = self.simulation_event_source.events(datetime(2018, 9, 14), datetime(2018, 9, 14), "tick")

            self.env.update_universe({"AU1812", "TF1812"})
            self.assertEvent(
                next(events), EVENT.BEFORE_TRADING,
                datetime(2018, 9, 13, 20, 29, 0, 500000), datetime(2018, 9, 14, 20, 29, 0, 500000)
            )

            self.env.update_universe({"TF1812"})
            self.assertEvent(
                next(events), EVENT.TICK,
                datetime(2018, 9, 14, 9, 14, 0, 400000), datetime(2018, 9, 14, 9, 14, 0, 400000),
                tick={"order_book_id": "TF1812"}
            )

            self.env.update_universe({"AU1812"})
            self.assertEvent(
                next(events), EVENT.TICK,
                datetime(2018, 9, 14, 9, 14, 3, 500000), datetime(2018, 9, 14, 9, 14, 3, 500000),
                tick={"order_book_id": "AU1812"}
            )
