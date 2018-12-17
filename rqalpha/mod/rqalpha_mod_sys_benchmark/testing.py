from rqalpha.utils.testing import DataProxyFixture
from rqalpha.mod.rqalpha_mod_sys_benchmark.benchmark_provider import BackTestPriceSeriesBenchmarkProvider


class PriceSeriesBenchmarkProviderFixture(DataProxyFixture):
    def __init__(self, *args, **kwargs):
        super(PriceSeriesBenchmarkProviderFixture, self).__init__(*args, **kwargs)

        self.benchmark_provider = None
        self.benchmark_order_book_id = None
        self.provider_class = BackTestPriceSeriesBenchmarkProvider

    def init_fixture(self):
        super(PriceSeriesBenchmarkProviderFixture, self).init_fixture()
        self.benchmark_provider = self.provider_class (self.benchmark_order_book_id)
