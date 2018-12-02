from rqalpha.utils.testing import DataProxyFixture


class BackTestPriceSeriesBenchmarkProviderFixture(DataProxyFixture):
    def __init__(self, *args, **kwargs):
        super(BackTestPriceSeriesBenchmarkProviderFixture, self).__init__(*args, **kwargs)

        self.benchmark_provider = None
        self.benchmark_order_book_id = None

    def init_fixture(self):
        from rqalpha.mod.rqalpha_mod_sys_benchmark.benchmark_provider import BackTestPriceSeriesBenchmarkProvider

        super(BackTestPriceSeriesBenchmarkProviderFixture, self).init_fixture()
        self.benchmark_provider = BackTestPriceSeriesBenchmarkProvider(self.benchmark_order_book_id)
