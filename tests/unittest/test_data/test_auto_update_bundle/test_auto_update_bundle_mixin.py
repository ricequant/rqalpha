# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import os
import datetime
import pickle
import tempfile

from rqalpha.utils.testing import DataProxyFixture, RQAlphaTestCase
from rqalpha.data.bundle import AutomaticUpdateBundle
from rqalpha.data.trading_dates_mixin import TradingDatesMixin


class AutomaticUpdateBundleTestCase(DataProxyFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(AutomaticUpdateBundleTestCase, self).__init__(*args, **kwargs)
        self._path = tempfile.TemporaryDirectory().name

    def init_fixture(self):
        super(AutomaticUpdateBundleTestCase, self).init_fixture()
        self._auto_update_bundle_module = AutomaticUpdateBundle(
            path=self._path,
            filename="open_auction_volume.h5",
            api=self._mock_get_open_auction_info,
            fields=['volume'],
            end_date=datetime.date(2024, 2, 28),
        )
        trading_dates_mixin = TradingDatesMixin(self.base_data_source.get_trading_calendars())
        self.base_data_source.batch_get_trading_date = trading_dates_mixin.batch_get_trading_date
        self.base_data_source.get_next_trading_date = trading_dates_mixin.get_next_trading_date

    def _mock_get_open_auction_info(self, order_book_id, *args, **kwargs):
        df = pickle.loads(open(
            os.path.join(os.path.dirname(__file__), "mock_data/mock_open_auction_info.pkl"), "rb"
        ).read())
        df = df.loc[order_book_id].reset_index()
        df['order_book_id'] = order_book_id
        df = df.set_index(["order_book_id", "datetime"])
        return df
    
    def _mock_get_open_auction_volume(self, instrument, dt):
        # type: (Instrument, datetime.date) -> float
        data = self._auto_update_bundle_module.get_data(instrument, dt)
        if data is None:
            volume = 0
        else:
            volume = 0 if len(data) == 0 else data['volume']
        return volume

    def test_auto_update_bundle(self):
        s_volume = self._mock_get_open_auction_volume(self.env.get_instrument("000001.XSHE"), datetime.date(2023, 12, 28))
        f_volume = self._mock_get_open_auction_volume(self.env.get_instrument("A2401"), datetime.date(2023, 12, 28))
        assert os.path.exists(os.path.join(self._path, "open_auction_volume.h5")) == True

        pickle_data = pickle.loads(open(
            os.path.join(os.path.dirname(__file__), "mock_data/mock_open_auction_info.pkl"), "rb"
        ).read())

        s_df = pickle_data.loc["000001.XSHE"]
        assert s_volume == s_df[s_df.index.date == datetime.date(2023, 12, 28)].volume[0]
        f_df = pickle_data.loc['A2401']
        # 期货由于有夜盘，open_auction_info 的时间为前一个交易日的晚上，即从 pickle 文件中获取时，date 应该提前一个交易日
        assert f_volume == f_df[f_df.index.date == datetime.date(2023, 12, 27)].volume[0]
        
