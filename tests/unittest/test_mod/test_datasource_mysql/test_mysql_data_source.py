import datetime

from rqalpha.model.instrument import Instrument
from rqalpha.utils.testing import RQAlphaTestCase
from rqalpha.mod.rqalpha_mod_datasource_mysql.mysql_data_source import MysqlDataSource


class DataSourceDailyDataTestCase(RQAlphaTestCase):
    def init_fixture(self):
        self.instrument = Instrument({'order_book_id':'000001.XSHE', 'type':'CS'})
        self.data_source = MysqlDataSource('C:/Users/louis.xu/.rqalpha/bundle', {})

    def test_get_bar(self):
        dt = datetime.date(year=2021, month=4, day=20)
        data = self.data_source.get_bar(self.instrument,dt , '1d')
        print(data)

    def test_history_bar(self):
        dt = datetime.date(year=2021, month=5, day=10)
        data = self.data_source.history_bars(self.instrument, 10, '1d', 'close', dt, adjust_type='none')
        print(data)