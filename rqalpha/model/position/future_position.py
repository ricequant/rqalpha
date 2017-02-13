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

import six

from .base_position import BasePosition
from ...execution_context import ExecutionContext
from ...environment import Environment
from ...const import ACCOUNT_TYPE, SIDE


FuturePersistMap = {
    "_order_book_id": "_order_book_id",
    "_last_price": "_last_price",
    "_market_value": "_market_value",
    "_buy_market_value": "_buy_market_value",
    "_sell_market_value": "_sell_market_value",
    "_buy_trade_value": "_buy_trade_value",
    "_sell_trade_value": "_sell_trade_value",
    "_buy_order_value": "_buy_order_value",
    "_sell_order_value": "_sell_order_value",
    "_buy_order_quantity": "_buy_order_quantity",
    "_sell_order_quantity": "_sell_order_quantity",
    "_buy_trade_quantity": "_buy_trade_quantity",
    "_sell_trade_quantity": "_sell_trade_quantity",
    "_total_orders": "_total_orders",
    "_total_trades": "_total_trades",
    "_is_traded": "_is_traded",
    "_buy_open_order_value": "_buy_open_order_value",
    "_sell_open_order_value": "_sell_open_order_value",
    "_buy_close_order_value": "_buy_close_order_value",
    "_sell_close_order_value": "_sell_close_order_value",
    "_buy_open_order_quantity": "_buy_open_order_quantity",
    "_sell_open_order_quantity": "_sell_open_order_quantity",
    "_buy_close_order_quantity": "_buy_close_order_quantity",
    "_sell_close_order_quantity": "_sell_close_order_quantity",
    "_buy_open_trade_quantity": "_buy_open_trade_quantity",
    "_sell_open_trade_quantity": "_sell_open_trade_quantity",
    "_buy_close_trade_quantity": "_buy_close_trade_quantity",
    "_sell_close_trade_quantity": "_sell_close_trade_quantity",
    "_daily_realized_pnl": "_daily_realized_pnl",
    "_prev_settle_price": "_prev_settle_price",
    "_buy_old_holding_list": "_buy_old_holding_list",
    "_sell_old_holding_list": "_sell_old_holding_list",
    "_buy_today_holding_list": "_buy_today_holding_list",
    "_sell_today_holding_list": "_sell_today_holding_list",
    "_contract_multiplier": "_contract_multiplier",
    "_de_listed_date": "_de_listed_date",
    "_buy_open_transaction_cost": "_buy_open_transaction_cost",
    "_buy_close_transaction_cost": "_buy_close_transaction_cost",
    "_sell_open_transaction_cost": "_sell_open_transaction_cost",
    "_sell_close_transaction_cost": "_sell_close_transaction_cost",
    "_buy_daily_realized_pnl": "_buy_daily_realized_pnl",
    "_sell_daily_realized_pnl": "_sell_daily_realized_pnl",
}


class FuturePosition(BasePosition):

    # buy_open_order_value:       <float> 买开挂单总值
    # sell_open_order_value:      <float> 卖开挂单总值
    # buy_close_order_value:      <float> 买平挂单总值
    # sell_close_order_value:     <float> 卖平挂单总值
    # buy_open_order_quantity:    <float> 买开挂单量
    # sell_open_order_quantity:   <float> 卖开挂单量
    # buy_close_order_quantity:   <float> 买平挂单量
    # sell_close_order_quantity:  <float> 卖平挂单量
    # buy_open_trade_quantity:    <float> 买开成交量
    # sell_open_trade_quantity:   <float> 卖开成交量
    # buy_close_trade_quantity:   <float> 买平成交量
    # sell_close_trade_quantity:  <float> 买平成交量
    # daily_realized_pnl:         <float> 当日平仓盈亏
    # buy_settle_holding:         <Tuple(price, amount)> 买结算后昨仓
    # sell_settle_holding:        <Tuple(price, amount)> 卖结算后昨仓
    # buy_today_holding_list:     <List<Tuple(price, amount)>> 买当日持仓队列
    # sell_today_holding_list:    <List<Tuple(price, amount)>> 卖当日持仓队列

    def __init__(self, order_book_id):
        super(FuturePosition, self).__init__(order_book_id)
        self._buy_open_order_value = 0.
        self._sell_open_order_value = 0.
        self._buy_close_order_value = 0.
        self._sell_close_order_value = 0.
        self._buy_open_order_quantity = 0
        self._sell_open_order_quantity = 0
        self._buy_close_order_quantity = 0
        self._sell_close_order_quantity = 0
        self._buy_open_trade_quantity = 0
        self._buy_open_trade_value = 0
        self._sell_open_trade_quantity = 0
        self._sell_open_trade_value = 0
        self._buy_close_trade_quantity = 0
        self._buy_close_trade_value = 0
        self._sell_close_trade_quantity = 0
        self._sell_close_trade_value = 0
        self._daily_realized_pnl = 0.
        self._prev_settle_price = 0.
        self._buy_old_holding_list = []         # [(price, amount)]
        self._sell_old_holding_list = []        # [(price, amount)]
        self._buy_today_holding_list = []       # [(price, amount)]
        self._sell_today_holding_list = []      # [(price, amount)]
        instrument = ExecutionContext.get_instrument(self.order_book_id)
        if instrument is None:
            self._contract_multiplier = None
            self._de_listed_date = None
        else:
            self._contract_multiplier = instrument.contract_multiplier
            self._de_listed_date = instrument.de_listed_date

        self._buy_open_transaction_cost = 0.
        self._buy_close_transaction_cost = 0.
        self._sell_open_transaction_cost = 0.
        self._sell_close_transaction_cost = 0.
        self._buy_daily_realized_pnl = 0.
        self._sell_daily_realized_pnl = 0.
        self._buy_avg_open_price = 0.
        self._sell_avg_open_price = 0.
        self._buy_market_value = 0.
        self._sell_market_value = 0.

    @classmethod
    def __from_dict__(cls, position_dict):
        position = cls(position_dict["_order_book_id"])
        for persist_key, origin_key in six.iteritems(FuturePersistMap):
            setattr(position, origin_key, position_dict[persist_key])
        return position

    def __to_dict__(self):
        p_dict = {}
        for persist_key, origin_key in six.iteritems(FuturePersistMap):
            p_dict[persist_key] = getattr(self, origin_key)
        return p_dict

    @property
    def buy_open_order_quantity(self):
        """
        【int】买开挂单量
        """
        return self._buy_open_order_quantity

    @property
    def sell_open_order_quantity(self):
        """
        【int】卖开挂单量
        """
        return self._sell_open_order_quantity

    @property
    def buy_close_order_quantity(self):
        """
        【int】买平挂单量
        """
        return self._buy_close_order_quantity

    @property
    def sell_close_order_quantity(self):
        """
        【int】卖平挂单量
        """
        return self._sell_close_order_quantity

    @property
    def daily_realized_pnl(self):
        """
        【float】当日平仓盈亏
        """
        return self._daily_realized_pnl

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，当日浮动盈亏+当日平仓盈亏
        """
        return self.daily_realized_pnl + self.daily_holding_pnl

    @property
    def daily_holding_pnl(self):
        """
        【float】当日持仓盈亏
        """
        # daily_holding_pnl: < float > 当日持仓盈亏
        return self._market_value + self._sell_holding_cost - self._buy_holding_cost

    @property
    def _buy_daily_holding_pnl(self):
        return (self._last_price - self.buy_avg_holding_price) * self.buy_quantity * self._contract_multiplier

    @property
    def _sell_daily_holding_pnl(self):
        return (self.sell_avg_holding_price - self._last_price) * self.sell_quantity * self._contract_multiplier

    @property
    def buy_daily_pnl(self):
        """
        【float】多头仓位当日盈亏
        """
        return self._buy_daily_holding_pnl + self._buy_daily_realized_pnl

    @property
    def sell_daily_pnl(self):
        """
        【float】空头仓位当日盈亏
        """
        return self._sell_daily_holding_pnl + self._sell_daily_realized_pnl

    @property
    def margin(self):
        """
        【float】仓位总保证金
        """
        # 总保证金
        # TODO 这里之后需要进行修改,需要考虑单向大边的情况
        return self.buy_margin + self.sell_margin

    @property
    def buy_margin(self):
        """
        【float】多头持仓占用保证金
        """
        # buy_margin: < float > 买保证金
        margin_decider = Environment.get_instance().accounts[ACCOUNT_TYPE.FUTURE].margin_decider
        return margin_decider.cal_margin(self.order_book_id, SIDE.BUY, self._buy_holding_cost)

    @property
    def sell_margin(self):
        """
        【float】空头持仓占用保证金
        """
        # sell_margin: < float > 卖保证金
        margin_decider = Environment.get_instance().accounts[ACCOUNT_TYPE.FUTURE].margin_decider
        return margin_decider.cal_margin(self.order_book_id, SIDE.SELL, self._sell_holding_cost)

    @property
    def _buy_old_holding_quantity(self):
        return sum(amount for price, amount in self._buy_old_holding_list)

    @property
    def _sell_old_holding_quantity(self):
        return sum(amount for price, amount in self._sell_old_holding_list)

    @property
    def _buy_today_holding_quantity(self):
        return sum(amount for price, amount in self._buy_today_holding_list)

    @property
    def _sell_today_holding_quantity(self):
        return sum(amount for price, amount in self._sell_today_holding_list)

    @property
    def buy_quantity(self):
        """
        【int】多头持仓
        """
        # 买方向总持仓
        return self._buy_old_holding_quantity + self._buy_today_holding_quantity

    @property
    def sell_quantity(self):
        """
        【int】空头持仓
        """
        # 卖方向总持仓
        return self._sell_old_holding_quantity + self._sell_today_holding_quantity

    @property
    def buy_avg_holding_price(self):
        """
        【float】多头持仓均价
        """
        return 0 if self.buy_quantity == 0 else self._buy_holding_cost / self.buy_quantity / self._contract_multiplier

    @property
    def sell_avg_holding_price(self):
        """
        【float】空头持仓均价
        """
        return 0 if self.sell_quantity == 0 else self._sell_holding_cost / self.sell_quantity / self._contract_multiplier

    @property
    def _buy_closable_quantity(self):
        # 买方向可平仓量
        return self.buy_quantity - self._sell_close_order_quantity

    @property
    def _sell_closable_quantity(self):
        # 卖方向可平仓量
        return self.sell_quantity - self._buy_close_order_quantity

    @property
    def closable_buy_quantity(self):
        """
        【float】可平多头持仓
        """
        return self._buy_closable_quantity

    @property
    def closable_sell_quantity(self):
        """
        【int】可平空头持仓
        """
        return self._sell_closable_quantity

    @property
    def _buy_old_holding_cost(self):
        return self._buy_old_holding_quantity * self._prev_settle_price * self._contract_multiplier

    @property
    def _sell_old_holding_cost(self):
        return self._sell_old_holding_quantity * self._prev_settle_price * self._contract_multiplier

    @property
    def _buy_today_holding_cost(self):
        return sum(p * a * self._contract_multiplier for p, a in self._buy_today_holding_list)

    @property
    def _sell_today_holding_cost(self):
        return sum(p * a * self._contract_multiplier for p, a in self._sell_today_holding_list)

    @property
    def _buy_holding_cost(self):
        return self._buy_old_holding_cost + self._buy_today_holding_cost

    @property
    def _sell_holding_cost(self):
        return self._sell_old_holding_cost + self._sell_today_holding_cost

    @property
    def _quantity(self):
        return self.buy_quantity + self.sell_quantity

    @property
    def _position_value(self):
        # 总保证金 + 当日持仓盈亏 + 当日平仓盈亏
        return self.margin + self.daily_holding_pnl + self.daily_realized_pnl

    @property
    def buy_today_quantity(self):
        """
        【int】多头今仓
        """
        # Buy今仓
        return sum(amount for (price, amount) in self._buy_today_holding_list)

    @property
    def sell_today_quantity(self):
        """
        【int】空头今仓
        """
        # Sell今仓
        return sum(amount for (price, amount) in self._sell_today_holding_list)

    @property
    def _closable_buy_today_quantity(self):
        return self.buy_today_quantity - self._sell_close_order_quantity

    @property
    def _closable_sell_today_quantity(self):
        return self.sell_today_quantity - self._buy_close_order_quantity

    @property
    def buy_pnl(self):
        """
        【float】多头仓位累计盈亏
        """
        return self._sell_close_trade_value - self._buy_open_trade_value + \
               self.buy_quantity * self._last_price * self._contract_multiplier

    @property
    def sell_pnl(self):
        """
        【float】空头仓位累计盈亏
        """
        return self._sell_open_trade_value - self._buy_close_trade_value - \
               self.sell_quantity * self._last_price * self._contract_multiplier

    @property
    def buy_daily_pnl(self):
        """
        【float】多头仓位当日盈亏
        """
        return self._buy_daily_holding_pnl + self._buy_daily_realized_pnl

    @property
    def sell_daily_pnl(self):
        """
        【float】空头仓位当日盈亏
        """
        return self._sell_daily_holding_pnl + self._sell_daily_realized_pnl

    @property
    def _buy_holding_list(self):
        return self._buy_old_holding_list + self._buy_today_holding_list

    @property
    def _sell_holding_list(self):
        return self._sell_old_holding_list + self._sell_today_holding_list

    @property
    def buy_avg_open_price(self):
        """
        【float】多头持仓均价
        """
        return self._buy_avg_open_price

    @property
    def sell_avg_open_price(self):
        """
        【float】空头开仓均价
        """
        return self._sell_avg_open_price

    @property
    def buy_transaction_cost(self):
        """
        【float】多头费用
        """
        return self._buy_open_transaction_cost + self._sell_close_transaction_cost

    @property
    def sell_transaction_cost(self):
        """
        【float】空头费用
        """
        return self._sell_open_transaction_cost + self._buy_close_transaction_cost

    @property
    def transaction_cost(self):
        """
        【float】仓位交易费用
        """
        return self.buy_transaction_cost + self.sell_transaction_cost

    @property
    def buy_market_value(self):
        """
        【float】多头仓位市值加总
        """
        return self._buy_market_value

    @property
    def sell_market_value(self):
        """
        【float】空头仓位市值加总
        """
        return self._sell_market_value

    def _cal_close_today_amount(self, trade_amount, trade_side):
        if trade_side == SIDE.SELL:
            close_today_amount = trade_amount - self._buy_old_holding_quantity
        else:
            close_today_amount = trade_amount - self._sell_old_holding_quantity
        return max(close_today_amount, 0)
