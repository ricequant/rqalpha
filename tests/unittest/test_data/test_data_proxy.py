from datetime import datetime
from math import isnan
from unittest.mock import Mock

from rqalpha.data.data_proxy import DataProxy
from rqalpha.utils.exception import InstrumentNotFound, MultipleInstrumentFound
from rqalpha.utils.testing import EnvironmentFixture, RQAlphaTestCase, mock_instrument


class DataProxyTestCase(EnvironmentFixture, RQAlphaTestCase):
    def init_fixture(self):
        super(DataProxyTestCase, self).init_fixture()
        self.data_source = Mock()
        self.data_proxy = DataProxy(self.data_source, Mock())
        self.env.set_data_proxy(self.data_proxy)

    @staticmethod
    def _make_instrument(order_book_id, listed_date, de_listed_date):
        return mock_instrument(
            order_book_id,
            listed_date=listed_date,
            de_listed_date=de_listed_date,
        )

    def _assert_nan_bar(self, bar, instrument, dt):
        self.assertIs(bar.instrument, instrument)
        self.assertTrue(isnan(bar.close))
        if dt is not None:
            self.assertEqual(bar.datetime, dt)

    def test_get_bar_uses_active_instrument_and_returns_source_bar(self):
        order_book_id = "000001.XSHE"
        dt = datetime(2024, 1, 2)
        retired_instrument = self._make_instrument(order_book_id, "2000-01-01", "2020-01-01")
        active_instrument = self._make_instrument(order_book_id, "2023-01-01", "2999-12-31")
        source_bar = {
            "datetime": dt,
            "open": 10.0,
            "close": 10.5,
            "high": 11.0,
            "low": 9.5,
        }
        self.data_source.get_instruments.return_value = [retired_instrument, active_instrument]
        self.data_source.get_bar.return_value = source_bar

        bar = self.data_proxy.get_bar(order_book_id, dt)

        self.data_source.get_instruments.assert_called_once_with(id_or_syms=[order_book_id])
        self.data_source.get_bar.assert_called_once_with(active_instrument, dt, "1d")
        self.assertIs(bar.instrument, active_instrument)
        self.assertEqual(bar.close, source_bar["close"])

    def test_get_bar_returns_nan_bar_for_most_recent_retired_instrument(self):
        order_book_id = "000001.XSHE"
        dt = datetime(2024, 1, 2)
        older_instrument = self._make_instrument(order_book_id, "2000-01-01", "2010-01-01")
        retired_instrument = self._make_instrument(order_book_id, "2015-01-01", "2020-01-01")
        self.data_source.get_instruments.return_value = [retired_instrument, older_instrument]

        bar = self.data_proxy.get_bar(order_book_id, dt)

        self._assert_nan_bar(bar, retired_instrument, dt)
        self.data_source.get_bar.assert_not_called()

    def test_get_bar_returns_nan_bar_for_earliest_pending_instrument(self):
        order_book_id = "000001.XSHE"
        dt = datetime(2024, 1, 2)
        pending_instrument = self._make_instrument(order_book_id, "2025-01-01", "2999-12-31")
        later_instrument = self._make_instrument(order_book_id, "2026-01-01", "2999-12-31")
        self.data_source.get_instruments.return_value = [later_instrument, pending_instrument]

        bar = self.data_proxy.get_bar(order_book_id, dt)

        self._assert_nan_bar(bar, pending_instrument, dt)
        self.data_source.get_bar.assert_not_called()

    def test_get_bar_raises_for_unknown_instrument(self):
        order_book_id = "UNKNOWN.XSHE"
        dt = datetime(2024, 1, 2)
        self.data_source.get_instruments.return_value = []

        with self.assertRaises(InstrumentNotFound):
            self.data_proxy.get_bar(order_book_id, dt)

        self.data_source.get_bar.assert_not_called()

    def test_get_bar_propagates_multiple_active_instrument_error(self):
        order_book_id = "000001.XSHE"
        dt = datetime(2024, 1, 2)
        first_active_instrument = self._make_instrument(order_book_id, "2020-01-01", "2999-12-31")
        second_active_instrument = self._make_instrument(order_book_id, "2023-01-01", "2999-12-31")
        self.data_source.get_instruments.return_value = [first_active_instrument, second_active_instrument]

        with self.assertRaises(MultipleInstrumentFound):
            self.data_proxy.get_bar(order_book_id, dt)

        self.data_source.get_bar.assert_not_called()

    def test_get_bar_without_datetime_uses_latest_historical_instrument(self):
        order_book_id = "000001.XSHE"
        older_instrument = self._make_instrument(order_book_id, "2000-01-01", "2010-01-01")
        latest_instrument = self._make_instrument(order_book_id, "2015-01-01", "2020-01-01")
        self.data_source.get_instruments.return_value = [latest_instrument, older_instrument]

        bar = self.data_proxy.get_bar(order_book_id, None)

        self._assert_nan_bar(bar, latest_instrument, None)
        self.data_source.get_bar.assert_not_called()

    def test_get_bar_without_datetime_raises_for_unknown_instrument(self):
        self.data_source.get_instruments.return_value = []

        with self.assertRaises(InstrumentNotFound):
            self.data_proxy.get_bar("UNKNOWN.XSHE", None)

        self.data_source.get_bar.assert_not_called()
