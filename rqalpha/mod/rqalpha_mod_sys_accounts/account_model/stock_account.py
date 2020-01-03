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

    def _on_before_trading(self, event):
        trading_date = Environment.get_instance().trading_dt.date()
        last_date = Environment.get_instance().data_proxy.get_previous_trading_date(trading_date)
        self._handle_dividend_book_closure(last_date)
        self._handle_dividend_payable(trading_date)
        self._handle_split(trading_date)
        self._handle_transform()

    def apply_settlement(self):
        env = Environment.get_instance()
        current_date = env.trading_dt
        next_date = env.data_proxy.get_next_trading_date(current_date)
        self._static_total_value = super(StockAccount, self).total_value

        for order_book_id, positions in list(six.iteritems(self._positions)):
            instrument = env.data_proxy.instruments(order_book_id)  # type: Instrument
            if positions[POSITION_DIRECTION.LONG].quantity == 0 and positions[POSITION_DIRECTION.SHORT] == 0:
                del self._positions[order_book_id]
            elif instrument.de_listed_at(next_date):
                try:
                    transform_data = env.data_proxy.get_share_transformation(order_book_id)
                except NotImplementedError:
                    pass
                else:
                    if transform_data is not None:
                        self._pending_transform[order_book_id] = transform_data
                        continue
                if not self.cash_return_by_stock_delisted:
                    self._static_total_value -= positions[POSITION_DIRECTION.LONG].market_value
                    self._static_total_value -= positions[POSITION_DIRECTION.SHORT].market_value
                user_system_log.warn(
                    _(u"{order_book_id} is expired, close all positions by system").format(
                        order_book_id=order_book_id)
                )
                self._positions.pop(order_book_id, None)
            else:
                for pos in six.itervalues(positions):
                    pos.apply_settlement()

        self._backward_trade_set.clear()

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK

    def get_state(self):
        state = super(StockAccount, self).get_state()
        state.update({
            'dividend_receivable': self._dividend_receivable,
            'pending_transform': self._pending_transform,
        })
        return state

    def set_state(self, state):
        super(StockAccount, self).set_state(state)
        self._dividend_receivable = state['dividend_receivable']
        self._pending_transform = state.get("pending_transform", {})

    def _handle_dividend_payable(self, trading_date):
        to_be_removed = []
        for order_book_id, dividend in six.iteritems(self._dividend_receivable):
            if dividend['payable_date'] == trading_date:
                to_be_removed.append(order_book_id)
                self._static_total_value += dividend['quantity'] * dividend['dividend_per_share']
        for order_book_id in to_be_removed:
            del self._dividend_receivable[order_book_id]

    @staticmethod
    def _int_to_date(d):
        r, d = divmod(d, 100)
        y, m = divmod(r, 100)
        return datetime.date(year=y, month=m, day=d)

    def _handle_dividend_book_closure(self, trading_date):
        for order_book_id, positions in six.iteritems(self._positions):
            dividend = Environment.get_instance().data_proxy.get_dividend_by_book_date(order_book_id, trading_date)
            if dividend is None:
                continue
            position = positions[POSITION_DIRECTION.LONG]  # type: AssetPosition
            if position.quantity == 0:
                continue

            dividend_per_share = sum(dividend['dividend_cash_before_tax'] / dividend['round_lot'])
            if np.isnan(dividend_per_share):
                raise RuntimeError("Dividend per share of {} is not supposed to be nan.".format(order_book_id))

            position.apply_dividend(dividend_per_share)

            if StockAccount.dividend_reinvestment:
                last_price = position.last_price
                dividend_value = position.quantity * dividend_per_share
                self._static_total_value += dividend_value
                self._apply_trade(Trade.__from_create__(
                    None, last_price, dividend_value / last_price, SIDE.BUY, POSITION_EFFECT.OPEN, order_book_id
                ))
            else:
                self._dividend_receivable[order_book_id] = {
                    'quantity': position.quantity,
                    'dividend_per_share': dividend_per_share,
                }

                try:
                    self._dividend_receivable[order_book_id]['payable_date'] = self._int_to_date(
                        dividend['payable_date'][0]
                    )
                except ValueError:
                    self._dividend_receivable[order_book_id]['payable_date'] = self._int_to_date(
                        dividend['ex_dividend_date'][0]
                    )

    def _handle_split(self, trading_date):
        data_proxy = Environment.get_instance().data_proxy
        for order_book_id, positions in six.iteritems(self._positions):
            ratio = data_proxy.get_split_by_ex_date(order_book_id, trading_date)
            if ratio is None:
                continue
            positions[POSITION_DIRECTION.LONG].apply_split(ratio)

    def _handle_transform(self):
        if not self._pending_transform:
            return
        for predecessor, (successor, conversion_ratio) in six.iteritems(self._pending_transform):
            predecessor_position = self._positions.pop(predecessor)[POSITION_DIRECTION.LONG]

            self._apply_trade(Trade.__from_create__(
                order_id=None,
                price=predecessor_position.avg_price / conversion_ratio,
                amount=predecessor_position.quantity * conversion_ratio,
                side=SIDE.BUY,
                position_effect=POSITION_EFFECT.OPEN,
                order_book_id=successor
            ))
            user_system_log.warn(_(u"{predecessor} code has changed to {successor}, change position by system").format(
                predecessor=predecessor, successor=successor))

        self._pending_transform.clear()

    def _get_or_create_pos(self, order_book_id, direction):
        # type: (str, POSITION_DIRECTION) -> AssetPosition
        if direction == POSITION_DIRECTION.SHORT:
            raise RuntimeError("StockAccount doesn't support short position")
        if order_book_id not in self._positions:
            positions = self._positions.setdefault(order_book_id, {
                POSITION_DIRECTION.LONG: AssetPosition(order_book_id, POSITION_DIRECTION.LONG, self.t1),
                POSITION_DIRECTION.SHORT: AssetPosition(order_book_id, POSITION_DIRECTION.SHORT, self.t1)
            })
        else:
            positions = self._positions[order_book_id]
        return positions[POSITION_DIRECTION.LONG]

    @property
    def dividend_receivable(self):
        """
        [float] 投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分
        """
        return sum(d['quantity'] * d['dividend_per_share'] for d in six.itervalues(self._dividend_receivable))

    @property
    def total_value(self):
        """
        [float] 股票账户总权益

        股票账户总权益 = 股票账户总资金 + 股票持仓总市值 + 应收分红

        """
        return super(StockAccount, self).total_value + self.dividend_receivable

    @property
    def positions(self):
        if not self._position_proxy_dict:
            self._position_proxy_dict = PositionProxyDict(self._positions, StockPositionProxy)
        return self._position_proxy_dict
