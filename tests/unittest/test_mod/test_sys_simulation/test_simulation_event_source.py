from unittest.mock import MagicMock

from datetime import datetime

from rqalpha.utils.testing import RQAlphaTestCase, DataProxyFixture
from rqalpha.mod.rqalpha_mod_sys_simulation.testing import SimulationEventSourceFixture


class SimulationEventSourceTestCase(SimulationEventSourceFixture, DataProxyFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(SimulationEventSourceTestCase, self).__init__(*args, **kwargs)

    def test_tick_events(self):
        with self.mock_env_method("get_universe", MagicMock(return_value={"RB1701"})):
            for event in self.simulation_event_source.events(datetime(2016, 1, 1), datetime(2016, 1, 5), "tick"):
                print(event)


