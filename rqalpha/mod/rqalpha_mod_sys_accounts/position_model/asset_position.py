# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from rqalpha.interface import AbstractPosition
from rqalpha.environment import Environment
from rqalpha.const import SIDE, POSITION_EFFECT, POSITION_DIRECTION
from rqalpha.utils.i18n import gettext as _

from rqalpha.utils.repr import property_repr
from rqalpha.utils import is_valid_price


class AssetPosition(object):

    __repr__ = property_repr

    def __init__(self, order_book_id, direction):
        self._order_book_id = order_book_id
        self._direction = direction

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
        self._market_tplus = None

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
    def trade_cost(self):
        return self._trade_cost

    @property
    def trading_pnl(self):
        # 今日交易产生的持仓差
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
    def market_tplus(self):
        if self._market_tplus is None:
            env = Environment.get_instance()
            self._market_tplus = env.data_proxy.instruments(self._order_book_id).market_tplus
        return self._market_tplus

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

            if self.market_tplus >= 1:
                self._non_closable += trade.last_quantity
            return 0
        else:
            if trade.position_effect == POSITION_EFFECT.CLOSE_TODAY:
                self._today_quantity -= trade.last_quantity
            elif trade.position_effect == POSITION_EFFECT.CLOSE:
                # 先平昨，后平今
                self._old_quantity -= trade.last_quantity
                if self._old_quantity < 0:
                    self._today_quantity += self._old_quantity
                    self._old_quantity = 0
            else:
                raise RuntimeError("Unknown position_effect of trade: {}".format(trade))
            self._trade_cost -= trade.last_price * trade.last_quantity

    def apply_split(self, ratio):
        self._today_quantity *= ratio
        self._old_quantity *= ratio
        self._avg_price /= ratio

    def apply_dividend(self, dividend_per_unit):
        self._avg_price -= dividend_per_unit

    def update_last_price(self, price):
        self._last_price = price


class AssetPositionProxy(AbstractPosition):
    __abandon_properties__ = [
        "positions",
        "long",
        "short"
    ]

    def __init__(self, order_book_id):
        self._long = AssetPosition(order_book_id, POSITION_DIRECTION.LONG)
        self._short = AssetPosition(order_book_id, POSITION_DIRECTION.SHORT)

    __repr__ = property_repr

    @property
    def type(self):
        raise NotImplementedError

    def get_state(self):
        """"""
        return {
            "order_book_id": self.order_book_id,
            "long": self._long.get_state(),
            "short": self._short.get_state()
        }

    def set_state(self, state):
        """"""
        self._long.set_state(state["long"])
        self._short.set_state(state["short"])

    @property
    def order_book_id(self):
        return self._long.order_book_id

    @property
    def last_price(self):
        return self._long.last_price

    @property
    def market_value(self):
        return self._long.market_value - self._short.market_value

    # -- PNL 相关
    @property
    def position_pnl(self):
        """
        [float] 昨仓盈亏，当前交易日盈亏中来源于昨仓的部分

        多方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (最新价 - 昨收价)
        空方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (昨收价 - 最新价)

        """
        return self._long.position_pnl + self._short.position_pnl

    @property
    def trading_pnl(self):
        """
        [float] 交易盈亏，当前交易日盈亏中来源于当日成交的部分

        单比买方向成交的交易盈亏 = 成交量 * (最新价 - 成交价)
        单比卖方向成交的交易盈亏 = 成交量 * (成交价 - 最新价)

        """
        return self._long.trading_pnl + self._short.trading_pnl

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏

        当日盈亏 = 昨仓盈亏 + 交易盈亏

        """
        return self._long.position_pnl + self._long.trading_pnl + self._short.position_pnl +\
               self._short.trading_pnl - self.transaction_cost

    @property
    def pnl(self):
        """
        [float] 累计盈亏

        (最新价 - 平均开仓价格) * 持仓量 * 合约乘数

        """
        return self._long.pnl + self._short.pnl

    # -- Quantity 相关
    @property
    def open_orders(self):
        return Environment.get_instance().broker.get_open_orders(self.order_book_id)

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 保证金

        保证金 = 持仓量 * 最新价 * 合约乘数 * 保证金率

        股票保证金 = 市值 = 持仓量 * 最新价

        """
        return self._long.margin + self._short.margin

    @property
    def transaction_cost(self):
        """
        [float] 交易费率
        """
        return self._long.transaction_cost + self._short.transaction_cost

    @property
    def positions(self):
        return [self._long, self._short]

    @property
    def long(self):
        return self._long

    @property
    def short(self):
        return self._short

    # -- Function
    def apply_settlement(self):
        self._long.apply_settlement()
        self._short.apply_settlement()

    def apply_trade(self, trade):
        if (
            trade.side == SIDE.BUY and trade.position_effect == POSITION_EFFECT.OPEN
        ) or (
            trade.side == SIDE.SELL and trade.position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY)
        ):
            return self._long.apply_trade(trade)
        else:
            return self._short.apply_trade(trade)

    def update_last_price(self):
        price = Environment.get_instance().get_last_price(self.order_book_id)
        if price == price:
            # 过滤掉 nan
            self._long.update_last_price(price)
            self._short.update_last_price(price)

    def is_de_listed(self):
        raise NotImplementedError
