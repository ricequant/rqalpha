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
from typing import Iterable

from rqalpha.interface import AbstractPosition
from rqalpha.environment import Environment
from rqalpha.const import POSITION_EFFECT, POSITION_DIRECTION
from rqalpha.model.order import Order
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import property_repr
from rqalpha.utils import is_valid_price


class AssetPosition(AbstractPosition):
    __repr__ = property_repr

    def __init__(self, order_book_id, direction, t_plus_enabled=True):
        self._order_book_id = order_book_id
        self._direction = direction
        self._t_plus_enabled = t_plus_enabled

        self._old_quantity = 0
        self._logical_old_quantity = 0
        self._today_quantity = 0

        self._avg_price = 0
        self._trade_cost = 0
        self._transaction_cost = 0

        self._non_closable = 0

        self._prev_close = None

        self._contract_multiplier = None
        self._margin_rate = None
        self._market_tplus_ = None

        self._last_price = float("NaN")

        self._direction_factor = 1 if direction == POSITION_DIRECTION.LONG else -1
        self._margin_multiplier = Environment.get_instance().config.base.margin_multiplier

    def get_state(self):
        return {
            "old_quantity": self._old_quantity,
            "logical_old_quantity": self._logical_old_quantity,
            "today_quantity": self._today_quantity,
            "avg_price": self._avg_price,
            "trade_cost": self._trade_cost,
            "transaction_cost": self._transaction_cost,
            "non_closable": self._non_closable,
            "prev_close": self._prev_close
        }

    def set_state(self, state):
        self._old_quantity = state.get("old_quantity", 0)
        self._logical_old_quantity = state.get("logical_old_quantity", self._old_quantity)
        self._today_quantity = state.get("today_quantity", 0)
        self._avg_price = state.get("avg_price", 0)
        self._trade_cost = state.get("trade_cost", 0)
        self._transaction_cost = state.get("transaction_cost", 0)
        self._non_closable = state.get("non_closable", 0)
        self._prev_close = state.get("prev_close")

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def direction(self):
        return self._direction

    @property
    def quantity(self):
        return self._old_quantity + self._today_quantity

    @property
    def old_quantity(self):
        return self._old_quantity

    @property
    def today_quantity(self):
        return self._today_quantity

    @property
    def logical_old_quantity(self):
        return self._logical_old_quantity

    @property
    def non_closable(self):
        return self._non_closable

    @property
    def avg_price(self):
        return self._avg_price

    @property
    def transaction_cost(self):
        return self._transaction_cost

    @property
    def trading_pnl(self):
        trade_quantity = self._today_quantity + (self._old_quantity - self._logical_old_quantity)
        return self.contract_multiplier * (trade_quantity * self.last_price - self._trade_cost) * self._direction_factor

    @property
    def position_pnl(self):
        quantity = self._logical_old_quantity
        if quantity == 0:
            return 0
        return quantity * self.contract_multiplier * (self.last_price - self.prev_close) * self._direction_factor

    @property
    def pnl(self):
        return (self.last_price - self.avg_price) * self.quantity * self.contract_multiplier * self._direction_factor

    @property
    def market_value(self):
        return self.quantity * self.last_price * self.contract_multiplier

    @property
    def margin(self):
        return self.margin_rate * self.market_value

    @property
    def contract_multiplier(self):
        if not self._contract_multiplier:
            env = Environment.get_instance()
            self._contract_multiplier = env.data_proxy.instruments(self._order_book_id).contract_multiplier
        return self._contract_multiplier

    @property
    def margin_rate(self):
        if not self._margin_rate:
            env = Environment.get_instance()
            margin_rate = env.data_proxy.instruments(self._order_book_id).margin_rate
            if margin_rate == 1:
                self._margin_rate = margin_rate
            else:
                self._margin_rate = margin_rate * self._margin_multiplier
        return self._margin_rate

    @property
    def prev_close(self):
        if not is_valid_price(self._prev_close):
            env = Environment.get_instance()
            self._prev_close = env.data_proxy.get_prev_close(self._order_book_id, env.trading_dt)
        return self._prev_close

    @property
    def last_price(self):
        if self._last_price != self._last_price:
            env = Environment.get_instance()
            self._last_price = env.data_proxy.get_last_price(self._order_book_id)
            if self._last_price != self._last_price:
                raise RuntimeError(_("last price of position {} is not supposed to be nan").format(self._order_book_id))
        return self._last_price

    @property
    def closable(self):
        order_quantity = sum(o for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        if self._t_plus_enabled:
            return self.quantity - order_quantity - self._non_closable
        return self.quantity - order_quantity

    @property
    def today_closable(self):
        return self.today_quantity - sum(
            o.unfilled_quantity for o in self._open_orders if o.position_effect == POSITION_EFFECT.CLOSE_TODAY
        )

    @property
    def _open_orders(self):
        # type: () -> Iterable[Order]
        for order in Environment.get_instance().broker.get_open_orders(self.order_book_id):
            if order.position_direction == self._direction:
                yield order

    @property
    def _market_tplus(self):
        if self._market_tplus_ is None:
            env = Environment.get_instance()
            self._market_tplus_ = env.data_proxy.instruments(self._order_book_id).market_tplus
        return self._market_tplus_

    def apply_settlement(self):
        self._old_quantity += self._today_quantity
        self._logical_old_quantity = self._old_quantity
        self._today_quantity = self._trade_cost = self._transaction_cost = self._non_closable = 0
        self._contract_multiplier = self._margin_rate = None
        self._prev_close = self.last_price

    def apply_trade(self, trade):
        self._transaction_cost += trade.transaction_cost
        if trade.position_effect == POSITION_EFFECT.OPEN:
            if self.quantity < 0:
                if trade.last_quantity <= -1 * self.quantity:
                    self._avg_price = 0
                else:
                    self._avg_price = trade.last_price
            else:
                self._avg_price = (self.quantity * self._avg_price + trade.last_quantity * trade.last_price) / (
                        self.quantity + trade.last_quantity
                )
            self._today_quantity += trade.last_quantity
            self._trade_cost += trade.last_price * trade.last_quantity

            if self._market_tplus >= 1:
                self._non_closable += trade.last_quantity
            return 0
        else:
            if trade.position_effect == POSITION_EFFECT.CLOSE_TODAY:
                self._today_quantity -= trade.last_quantity
            else:
                # CLOSE, EXERCISE, MATCH, 先平昨，后平今
                self._old_quantity -= trade.last_quantity
                if self._old_quantity < 0:
                    self._today_quantity += self._old_quantity
                    self._old_quantity = 0
            if trade.position_effect == POSITION_EFFECT.MATCH:
                self._trade_cost -= self.last_price * trade.last_quantity
            else:
                self._trade_cost -= trade.last_price * trade.last_quantity

    def apply_split(self, ratio):
        self._today_quantity *= ratio
        self._old_quantity *= ratio
        self._avg_price /= ratio

    def apply_dividend(self, dividend_per_unit):
        self._avg_price -= dividend_per_unit

    def update_last_price(self, price):
        self._last_price = price
