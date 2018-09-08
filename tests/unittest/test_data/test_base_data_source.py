from rqalpha.utils.testing import BaseDataSourceFixture, RQAlphaTestCase, mock_instrument


class BaseDataSourceTestCase(BaseDataSourceFixture, RQAlphaTestCase):
    def test_get_tick_size(self):
        with self.mock_env_get_last_price(return_value=0.03):
            self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(exchange="XHKG")), 0.001)
        with self.mock_env_get_last_price(return_value=50):
            self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(exchange="XHKG")), 0.05)
        with self.mock_env_get_last_price(return_value=9999):
            self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(exchange="XHKG")), 5)
        self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(exchange="XSHE")), 0.01)
        self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(_type="FenjiA")), 0.001)
        self.assertEqual(self.base_data_source.get_tick_size(mock_instrument(_type="INDX")), 0.01)
        self.assertEqual(self.base_data_source.get_tick_size(
            mock_instrument(_type="Future", underlying_symbol="SM")
        ), 2)
        with self.assertRaises(RuntimeError):
            self.base_data_source.get_tick_size(mock_instrument(_type=None))
