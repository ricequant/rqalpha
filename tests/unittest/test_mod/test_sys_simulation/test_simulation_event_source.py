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
        from rqalpha.events import EVENT

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
