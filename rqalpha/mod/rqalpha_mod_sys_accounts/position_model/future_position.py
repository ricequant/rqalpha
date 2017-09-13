# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha.model.base_position import BasePosition
from rqalpha.environment import Environment
from rqalpha.const import SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE


class FuturePosition(BasePosition):

    __abandon_properties__ = []

    def __init__(self, order_book_id):
        super(FuturePosition, self).__init__(order_book_id)
        self._buy_old_holding_list = []
        self._sell_old_holding_list = []
        self._buy_today_holding_list = []
        self._sell_today_holding_list = []
        self._buy_transaction_cost = 0.
        self._sell_transaction_cost = 0.
        self._buy_realized_pnl = 0.
        self._sell_realized_pnl = 0.

        self._buy_avg_open_price = 0.
        self._sell_avg_open_price = 0.

    def __repr__(self):
        return 'FuturePosition({})'.format(self.__dict__)

    def get_state(self):
        return {
            'order_book_id': self._order_book_id,
            'buy_old_holding_list': self._buy_old_holding_list,
            'sell_old_holding_list': self._sell_old_holding_list,
            'buy_today_holding_list': self._buy_today_holding_list,
            'sell_today_holding_list': self._sell_today_holding_list,
            'buy_transaction_cost': self._buy_transaction_cost,
            'sell_transaction_cost': self._sell_transaction_cost,
            'buy_realized_pnl': self._buy_realized_pnl,
            'sell_realized_pnl': self._sell_realized_pnl,
            'buy_avg_open_price': self._buy_avg_open_price,
            'sell_avg_open_price': self._sell_avg_open_price,
            # margin rate may change
            'margin_rate': self.margin_rate,
        }

    def set_state(self, state):
        assert self._order_book_id == state['order_book_id']
        self._buy_old_holding_list = state['buy_old_holding_list']
        self._sell_old_holding_list = state['sell_old_holding_list']
        self._buy_today_holding_list = state['buy_today_holding_list']
        self._sell_today_holding_list = state['sell_today_holding_list']
        self._buy_transaction_cost = state['buy_transaction_cost']
        self._sell_transaction_cost = state['sell_transaction_cost']
        self._buy_avg_open_price = state['buy_avg_open_price']
        self._sell_avg_open_price = state['sell_avg_open_price']

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE.name

    @property
    def margin_rate(self):
        env = Environment.get_instance()
        margin_info = env.data_proxy.get_margin_info(self.order_book_id)
        margin_multiplier = env.config.base.margin_multiplier
        return margin_info['long_margin_ratio'] * margin_multiplier

    @property
    def market_value(self):
        return (self.buy_quantity - self.sell_quantity) * self.last_price * self.contract_multiplier

    @property
    def buy_market_value(self):
        return self.buy_quantity * self.last_price * self.contract_multiplier

    @property
    def sell_market_value(self):
        return self.sell_quantity * self.last_price * self.contract_multiplier

    # -- PNL 相关
    @property
    def contract_multiplier(self):
        return Environment.get_instance().get_instrument(self.order_book_id).contract_multiplier

    @property
    def open_orders(self):
        return Environment.get_instance().broker.get_open_orders(self.order_book_id)

    @property
    def buy_holding_pnl(self):
        """
        [float] 买方向当日持仓盈亏
        """
        return (self.last_price - self.buy_avg_holding_price) * self.buy_quantity * self.contract_multiplier

    @property
    def sell_holding_pnl(self):
        """
        [float] 卖方向当日持仓盈亏
        """
        return (self.sell_avg_holding_price - self.last_price) * self.sell_quantity * self.contract_multiplier

    @property
    def buy_realized_pnl(self):
        """
        [float] 买方向平仓盈亏
        """
        return self._buy_realized_pnl

    @property
    def sell_realized_pnl(self):
        """
        [float] 卖方向平仓盈亏
        """
        return self._sell_realized_pnl

    @property
    def holding_pnl(self):
        """
        [float] 当日持仓盈亏
        """
        return self.buy_holding_pnl + self.sell_holding_pnl

    @property
    def realized_pnl(self):
        """
        [float] 当日平仓盈亏
        """
        return self.buy_realized_pnl + self.sell_realized_pnl

    @property
    def buy_daily_pnl(self):
        """
        [float] 当日买方向盈亏
        """
        return self.buy_holding_pnl + self.buy_realized_pnl

    @property
    def sell_daily_pnl(self):
        """
        [float] 当日卖方向盈亏
        """
        return self.sell_holding_pnl + self.sell_realized_pnl

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.holding_pnl + self.realized_pnl

    @property
    def buy_pnl(self):
        """
        [float] 买方向累计盈亏
        """
        return (self.last_price - self._buy_avg_open_price) * self.buy_quantity * self.contract_multiplier

    @property
    def sell_pnl(self):
        """
        [float] 卖方向累计盈亏
        """
        return (self._sell_avg_open_price - self.last_price) * self.sell_quantity * self.contract_multiplier

    @property
    def pnl(self):
        """
        [float] 累计盈亏
        """
        return self.buy_pnl + self.sell_pnl

    # -- Quantity 相关
    @property
    def buy_open_order_quantity(self):
        """
        [int] 买方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if
                   order.side == SIDE.BUY and order.position_effect == POSITION_EFFECT.OPEN)

    @property
    def sell_open_order_quantity(self):
        """
        [int] 卖方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if
                   order.side == SIDE.SELL and order.position_effect == POSITION_EFFECT.OPEN)

    @property
    def buy_close_order_quantity(self):
        """
        [int] 买方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if order.side == SIDE.BUY and
                   order.position_effect in [POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY])

    @property
    def sell_close_order_quantity(self):
        """
        [int] 卖方向挂单量
        """
        return sum(order.unfilled_quantity for order in self.open_orders if order.side == SIDE.SELL and
                   order.position_effect in [POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY])

    @property
    def buy_old_quantity(self):
        """
        [int] 买方向昨仓
        """
        return sum(amount for price, amount in self._buy_old_holding_list)

    @property
    def sell_old_quantity(self):
        """
        [int] 卖方向昨仓
        """
        return sum(amount for price, amount in self._sell_old_holding_list)

    @property
    def buy_today_quantity(self):
        """
        [int] 买方向今仓
        """
        return sum(amount for price, amount in self._buy_today_holding_list)

    @property
    def sell_today_quantity(self):
        """
        [int] 卖方向今仓
        """
        return sum(amount for price, amount in self._sell_today_holding_list)

    @property
    def buy_quantity(self):
        """
        [int] 买方向持仓
        """
        return self.buy_old_quantity + self.buy_today_quantity

    @property
    def sell_quantity(self):
        """
        [int] 卖方向持仓
        """
        return self.sell_old_quantity + self.sell_today_quantity

    @property
    def closable_buy_quantity(self):
        """
        [float] 可平买方向持仓
        """
        return self.buy_quantity - self.sell_close_order_quantity

    @property
    def closable_sell_quantity(self):
        """
        [float] 可平卖方向持仓
        """
        return self.sell_quantity - self.buy_close_order_quantity

    # -- Margin 相关
    @property
    def buy_margin(self):
        """
        [float] 买方向持仓保证金
        """
        return self._buy_holding_cost * self.margin_rate

    @property
    def sell_margin(self):
        """
        [float] 卖方向持仓保证金
        """
        return self._sell_holding_cost * self.margin_rate

    @property
    def margin(self):
        """
        [float] 保证金
        """
        # TODO: 需要添加单向大边相关的处理逻辑
        return self.buy_margin + self.sell_margin

    @property
    def buy_avg_holding_price(self):
        """
        [float] 买方向持仓均价
        """
        return 0 if self.buy_quantity == 0 else self._buy_holding_cost / self.buy_quantity / self.contract_multiplier

    @property
    def sell_avg_holding_price(self):
        """
        [float] 卖方向持仓均价
        """
        return 0 if self.sell_quantity == 0 else self._sell_holding_cost / self.sell_quantity / self.contract_multiplier

    @property
    def _buy_holding_cost(self):
        return sum(p * a * self.contract_multiplier for p, a in self.buy_holding_list)

    @property
    def _sell_holding_cost(self):
        return sum(p * a * self.contract_multiplier for p, a in self.sell_holding_list)

    @property
    def buy_holding_list(self):
        return self._buy_old_holding_list + self._buy_today_holding_list

    @property
    def sell_holding_list(self):
        return self._sell_old_holding_list + self._sell_today_holding_list

    @property
    def buy_avg_open_price(self):
        return self._buy_avg_open_price

    @property
    def sell_avg_open_price(self):
        return self._sell_avg_open_price

    @property
    def buy_transaction_cost(self):
        return self._buy_transaction_cost

    @property
    def sell_transaction_cost(self):
        return self._sell_transaction_cost

    @property
    def transaction_cost(self):
        return self._buy_transaction_cost + self._sell_transaction_cost

    # -- Function

    def cal_close_today_amount(self, trade_amount, trade_side):
        if trade_side == SIDE.SELL:
            close_today_amount = trade_amount - self.buy_old_quantity
        else:
            close_today_amount = trade_amount - self.sell_old_quantity
        return max(close_today_amount, 0)

    def apply_settlement(self):
        env = Environment.get_instance()
        data_proxy = env.data_proxy
        trading_date = env.trading_dt.date()
        settle_price = data_proxy.get_settle_price(self.order_book_id, trading_date)
        self._buy_old_holding_list = [(settle_price, self.buy_quantity)]
        self._sell_old_holding_list = [(settle_price, self.sell_quantity)]
        self._buy_today_holding_list = []
        self._sell_today_holding_list = []

        self._buy_transaction_cost = 0.
        self._sell_transaction_cost = 0.
        self._buy_realized_pnl = 0.
        self._sell_realized_pnl = 0.

    def _margin_of(self, quantity, price):
        env = Environment.get_instance()
        instrument = env.data_proxy.instruments(self.order_book_id)
        return quantity * instrument.contract_multiplier * price * self.margin_rate

    def apply_trade(self, trade):
        trade_quantity = trade.last_quantity
        if trade.side == SIDE.BUY:
            if trade.position_effect == POSITION_EFFECT.OPEN:
                self._buy_avg_open_price = (self._buy_avg_open_price * self.buy_quantity +
                                            trade_quantity * trade.last_price) / (self.buy_quantity + trade_quantity)
                self._buy_transaction_cost += trade.transaction_cost
                self._buy_today_holding_list.insert(0, (trade.last_price, trade_quantity))
                return -1 * self._margin_of(trade_quantity, trade.last_price)
            else:
                old_margin = self.margin
                self._sell_transaction_cost += trade.transaction_cost
                delta_realized_pnl = self._close_holding(trade)
                self._sell_realized_pnl += delta_realized_pnl
                return old_margin - self.margin + delta_realized_pnl
        else:
            if trade.position_effect == POSITION_EFFECT.OPEN:
                self._sell_avg_open_price = (self._sell_avg_open_price * self.sell_quantity +
                                             trade_quantity * trade.last_price) / (self.sell_quantity + trade_quantity)
                self._sell_transaction_cost += trade.transaction_cost
                self._sell_today_holding_list.insert(0, (trade.last_price, trade_quantity))
                return -1 * self._margin_of(trade_quantity, trade.last_price)
            else:
                old_margin = self.margin
                self._buy_transaction_cost += trade.transaction_cost
                delta_realized_pnl = self._close_holding(trade)
                self._buy_realized_pnl += delta_realized_pnl
                return old_margin - self.margin + delta_realized_pnl

    def _close_holding(self, trade):
        left_quantity = trade.last_quantity
        delta = 0
        if trade.side == SIDE.BUY:
            # 先平昨仓
            if len(self._sell_old_holding_list) != 0:
                old_price, old_quantity = self._sell_old_holding_list.pop()

                if old_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._sell_old_holding_list = [(old_price, old_quantity - left_quantity)]
                else:
                    consumed_quantity = old_quantity
                left_quantity -= consumed_quantity
                delta += self._cal_realized_pnl(old_price, trade.last_price, trade.side, consumed_quantity)
            # 再平进仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = self._sell_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._sell_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta += self._cal_realized_pnl(oldest_price, trade.last_price, trade.side, consumed_quantity)
        else:
            # 先平昨仓
            if len(self._buy_old_holding_list) != 0:
                old_price, old_quantity = self._buy_old_holding_list.pop()
                if old_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._buy_old_holding_list = [(old_price, old_quantity - left_quantity)]
                else:
                    consumed_quantity = old_quantity
                left_quantity -= consumed_quantity
                delta += self._cal_realized_pnl(old_price, trade.last_price, trade.side, consumed_quantity)
            # 再平今仓
            while True:
                if left_quantity <= 0:
                    break
                oldest_price, oldest_quantity = self._buy_today_holding_list.pop()
                if oldest_quantity > left_quantity:
                    consumed_quantity = left_quantity
                    self._buy_today_holding_list.append((oldest_price, oldest_quantity - left_quantity))
                    left_quantity = 0
                else:
                    consumed_quantity = oldest_quantity
                left_quantity -= consumed_quantity
                delta += self._cal_realized_pnl(oldest_price, trade.last_price, trade.side, consumed_quantity)
        return delta

    def _cal_realized_pnl(self, cost_price, trade_price, side, consumed_quantity):
        if side == SIDE.BUY:
            return (cost_price - trade_price) * consumed_quantity * self.contract_multiplier
        else:
            return (trade_price - cost_price) * consumed_quantity * self.contract_multiplier
