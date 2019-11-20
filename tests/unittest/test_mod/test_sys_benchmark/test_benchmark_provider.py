from datetime import date, datetime, time

from rqalpha.utils.testing import RQAlphaTestCase
from rqalpha.mod.rqalpha_mod_sys_benchmark.testing import PriceSeriesBenchmarkProviderFixture
from rqalpha.events import EVENT, Event


class BackTestPriceSeriesBenchmarkProviderTestCase(PriceSeriesBenchmarkProviderFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(BackTestPriceSeriesBenchmarkProviderTestCase, self).__init__(*args, **kwargs)
        self.benchmark_order_book_id = "000300.XSHG"
        self.env_config["base"].update({
            "start_date": date(2018, 9, 3), "end_date": date(2018, 9, 25)
        })

    def test_returns(self):
        self.env.event_bus.publish_event(Event(EVENT.POST_SYSTEM_INIT))
        self.assertEqual(self.benchmark_provider.daily_returns, 0)
        self.env.event_bus.publish_event(Event(EVENT.AFTER_TRADING))
        self.assertAlmostEqual(self.benchmark_provider.daily_returns, (3321.82 - 3334.50) / 3334.50)
        self.assertAlmostEqual(self.benchmark_provider.total_returns, (3321.82 - 3334.50) / 3334.50)
        for i in range(10):
            self.env.event_bus.publish_event(Event(EVENT.AFTER_TRADING))
        self.assertAlmostEqual(self.benchmark_provider.daily_returns, (3204.92 - 3242.09) / 3242.09)
        self.assertAlmostEqual(self.benchmark_provider.total_returns, (3204.92 - 3334.50) / 3334.50)


if __name__ == "__main__":
    import unittest
    unittest.main()
