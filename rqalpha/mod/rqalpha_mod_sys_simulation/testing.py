from rqalpha.utils.testing import RQAlphaFixture


class SimulationEventSourceFixture(RQAlphaFixture):
    def __init__(self, *args, **kwargs):
        super(SimulationEventSourceFixture, self).__init__(*args, **kwargs)

    def init_fixture(self):
        pass
