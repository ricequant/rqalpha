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

from rqalpha.environment import Environment
from rqalpha.model.asset_account import AssetAccount
from rqalpha.model.asset_position import AssetPosition
from rqalpha.model.instrument import Instrument
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_EFFECT, SIDE, POSITION_DIRECTION
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.utils.i18n import gettext as _

from ..api.api_future import order
from .position_proxy import FuturePositionProxy, PositionProxyDict


class FutureAccount(AssetAccount):

    forced_liquidation = True

    __abandon_properties__ = [
        "holding_pnl",
        "realized_pnl",
    ]

    def __init__(self, total_cash, positions=None, backward_trade_set=None):
        super(FutureAccount, self).__init__(total_cash, positions, backward_trade_set)
        self._position_proxy_dict = None

    def order(self, order_book_id, quantity, style, target=False):
        long_position = self._positions[order_book_id][POSITION_DIRECTION.LONG]  # type: AssetPosition
        short_position = self._positions[order_book_id][POSITION_DIRECTION.SHORT]  # type: AssetPosition
        if target:
            # For order_to
            quantity -= (long_position.quantity - short_position.quantity)
        orders = []

        if quantity > 0:
            old_to_be_close, today_to_be_close = short_position.old_quantity, short_position.today_quantity
            side = SIDE.BUY
        else:
            old_to_be_close, today_to_be_close = long_position.old_quantity, long_position.today_quantity
            side = SIDE.SELL

        if old_to_be_close > 0:
            orders.append(order(order_book_id, min(quantity, old_to_be_close), side, POSITION_EFFECT.CLOSE, style))
            quantity -= old_to_be_close
        if quantity <= 0:
            return orders
        if today_to_be_close > 0:
            orders.append(order(
                order_book_id, min(quantity, today_to_be_close), side, POSITION_EFFECT.CLOSE_TODAY, style
            ))
            quantity -= today_to_be_close
        if quantity <= 0:
            return orders
        orders.append(order(order_book_id, quantity, side, POSITION_EFFECT.OPEN, style))
        return orders

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        # type: (str, float, POSITION_DIRECTION) -> float
        position = self._get_or_create_pos(order_book_id, position_direction)
        close_today_amount = trade_amount - position.old_quantity
        return max(close_today_amount, 0)

    def apply_settlement(self):
        env = Environment.get_instance()
        current_date = env.trading_dt
        next_date = env.data_proxy.get_next_trading_date(current_date)

        self._static_total_value = self.total_value

        for order_book_id, positions in list(six.iteritems(self._positions)):
            instrument = env.data_proxy.instruments(order_book_id)  # type: Instrument
            if positions[POSITION_DIRECTION.LONG].quantity == 0 and positions[POSITION_DIRECTION.SHORT] == 0:
                del self._positions[order_book_id]
            elif instrument.de_listed_at(next_date):
                user_system_log.warn(
                    _(u"{order_book_id} is expired, close all positions by system").format(order_book_id=order_book_id))
                del self._positions[order_book_id]
            else:
                for pos in six.itervalues(positions):
                    pos.apply_settlement()

        # 如果 total_value <= 0 则认为已爆仓，清空仓位，资金归0
        if self._static_total_value <= 0 and self.forced_liquidation:
            if self._positions:
                user_system_log.warn(_("Trigger Forced Liquidation, current total_value is 0"))
            self._positions.clear()
            self._static_total_value = 0

        self._backward_trade_set.clear()

    def _on_before_trading(self, event):
        pass

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE

    @property
    def buy_margin(self):
        # type: () -> float
        # 多方向保证金
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.LONG))

    @property
    def sell_margin(self):
        # type: () -> float
        # [float] 空方向保证金
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.SHORT))

    @property
    def positions(self):
        if not self._position_proxy_dict:
            self._position_proxy_dict = PositionProxyDict(self._positions, FuturePositionProxy)
        return self._position_proxy_dict

    # deprecated propertie
    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
