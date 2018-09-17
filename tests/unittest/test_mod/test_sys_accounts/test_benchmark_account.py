from rqalpha.utils.testing import RQAlphaTestCase, mock_instrument, mock_bar, mock_tick
from rqalpha.mod.rqalpha_mod_sys_accounts.testing import BenchmarkAccountFixture


class ModSysAccountsBenchmarkAccountTestCase(BenchmarkAccountFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(ModSysAccountsBenchmarkAccountTestCase, self).__init__(*args, **kwargs)
        self.benchmark = "000300,XSHG"
        self.env_config = {
            "base": {
                "benchmark": self.benchmark
            }
        }

    def test_on_bar(self):
        from rqalpha.events import EVENT, Event

        self.assertEqual(self.benchmark_account.total_value, self.benchmark_account_total_cash)
        self.assertEqual(len(self.benchmark_account.positions), 0)

        mock_event = Event(EVENT.PRE_BAR, bar_dict={
            self.benchmark: mock_bar(
                mock_instrument(self.benchmark), close=3000
            )
        })

        self.env.event_bus.publish_event(mock_event)

        self.assertAlmostEqual(self.benchmark_account.positions[self.benchmark].quantity, 4000 / 3000)
        self.env.event_bus.publish_event(mock_event)
        self.assertAlmostEqual(self.benchmark_account.positions[self.benchmark].quantity, 4000 / 3000)

    def test_on_tick(self):
        from rqalpha.events import EVENT, Event

        self.assertEqual(self.benchmark_account.total_value, self.benchmark_account_total_cash)
        self.assertEqual(len(self.benchmark_account.positions), 0)

        mock_event = Event(EVENT.TICK, tick=mock_tick(mock_instrument(self.benchmark), last=3000))

        self.env.event_bus.publish_event(mock_event)

        self.assertAlmostEqual(self.benchmark_account.positions[self.benchmark].quantity, 4000 / 3000)
        self.env.event_bus.publish_event(mock_event)
        self.assertAlmostEqual(self.benchmark_account.positions[self.benchmark].quantity, 4000 / 3000)
