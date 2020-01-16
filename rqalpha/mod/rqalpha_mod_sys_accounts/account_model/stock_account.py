# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import six
import datetime

import numpy as np

from rqalpha.environment import Environment
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.const import SIDE, DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, POSITION_DIRECTION
from rqalpha.model.trade import Trade
from rqalpha.model.asset_account import AssetAccount
from rqalpha.model.asset_position import AssetPosition
from rqalpha.model.instrument import Instrument

from ..api.api_stock import order_shares
from .position_proxy import StockPositionProxy, PositionProxyDict


class StockAccount(AssetAccount):

    dividend_reinvestment = False
    cash_return_by_stock_delisted = True
    t1 = True

    __abandon_properties__ = []

    def __init__(self, total_cash, positions=None, backward_trade_set=None, dividend_receivable=None):
        super(StockAccount, self).__init__(total_cash, positions, backward_trade_set)
        self._dividend_receivable = dividend_receivable or {}
        self._pending_transform = {}
        self._position_proxy_dict = None

    def order(self, order_book_id, quantity, style, target=False):
        position = self._positions[order_book_id][POSITION_DIRECTION]
        if target:
            # For order_to
            quantity = quantity - position.quantity
        return order_shares(order_book_id, quantity, style=style)

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        # type: (str, str, POSITION_DIRECTION) -> float
        return 0

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK

    @property
    def positions(self):
        if not self._position_proxy_dict:
            self._position_proxy_dict = PositionProxyDict(self._positions, StockPositionProxy)
        return self._position_proxy_dict
