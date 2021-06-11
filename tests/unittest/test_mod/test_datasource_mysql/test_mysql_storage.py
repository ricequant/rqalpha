import os
import pickle
from datetime import datetime

from rqalpha.mod.rqalpha_mod_datasource_mysql.models import StockDataDaily
from rqalpha.utils.testing import RQAlphaTestCase, DataProxyFixture, UniverseFixture
from rqalpha.mod.rqalpha_mod_sys_simulation.testing import SimulationEventSourceFixture
from rqalpha.mod.rqalpha_mod_datasource_mysql.storages import DayBarStore


class StorageDailyDataTestCase(RQAlphaTestCase):

    def init_fixture(self):
        self.order_book_id = '000001.XSHE'

    def test_get_bars(self):
        model = StockDataDaily
        data = DayBarStore(model).get_bars(self.order_book_id)
        print(data)

    def test_get_date_range(self):
        model = StockDataDaily
        data = DayBarStore(model).get_date_range(self.order_book_id)
        print(data)




