from rqalpha.utils.testing import DataProxyFixture, RQAlphaTestCase


class TradingDateMixinTestCase(DataProxyFixture, RQAlphaTestCase):
    def init_fixture(self):
        super(TradingDateMixinTestCase, self).init_fixture()

    def test_count_trading_dates(self):
        from datetime import date

        assert self.data_proxy.count_trading_dates(date(2018, 11, 1), date(2018, 11, 12)) == 8
        assert self.data_proxy.count_trading_dates(date(2018, 11, 3), date(2018, 11, 12)) == 6
        assert self.data_proxy.count_trading_dates(date(2018, 11, 3), date(2018, 11, 18)) == 10
