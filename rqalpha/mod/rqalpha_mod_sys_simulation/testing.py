from rqalpha.utils.testing import EnvironmentFixture


class SimulationEventSourceFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(SimulationEventSourceFixture, self).__init__(*args, **kwargs)
        self.simulation_event_source = None

    def init_fixture(self):
        from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_event_source import SimulationEventSource
        
        super(SimulationEventSourceFixture, self).init_fixture()
        self.simulation_event_source = SimulationEventSource(self.env)
