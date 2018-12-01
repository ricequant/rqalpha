from rqalpha.utils.testing import DataProxyFixture


class BackTestPriceSeriesBenchmarkPortfolioFixture(DataProxyFixture):
    def __init__(self, *args, **kwargs):
        super(BackTestPriceSeriesBenchmarkPortfolioFixture, self).__init__(*args, **kwargs)

        self.benchmark_portfolio = None
        self.benchmark_order_book_id = None

    def init_fixture(self):
        from rqalpha.mod.rqalpha_mod_sys_benchmark.benchmark_portfolio import BackTestPriceSeriesBenchmarkPortfolio

        super(BackTestPriceSeriesBenchmarkPortfolioFixture, self).init_fixture()
        self.benchmark_portfolio = BackTestPriceSeriesBenchmarkPortfolio(self.benchmark_order_book_id)
