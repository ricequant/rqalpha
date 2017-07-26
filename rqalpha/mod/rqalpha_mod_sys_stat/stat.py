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

import numpy as np
from collections import defaultdict

from rqalpha.const import POSITION_EFFECT, SIDE
from rqalpha.utils.repr import property_repr


class Stat(object):
    __repr__ = property_repr

    def __init__(self):
        self.buy_positions = defaultdict(list)
        self.sell_positions = defaultdict(list)

        # 多头回转交易手数
        self._rotary_buy_count = 0
        # 空头回转交易手数
        self._rotary_sell_count = 0
        # 盈利回转交易手数
        self._rotary_win_count = 0
        # 亏损回转交易手数
        self._rotary_loss_count = 0
        # 总盈利金额
        self._total_win_value = 0
        # 总亏损金额
        self._total_loss_value = 0
        # 总手续费
        self._total_cost = 0
        # 最大盈利金额/每手
        self._max_win_value = 0
        # 最大亏损金额/每手
        self._max_loss_value = 0
        # 多头持仓时间
        self._total_buy_position_seconds = 0
        # 空头持仓时间
        self._total_sell_position_seconds = 0
        # 盈利持仓时间
        self._total_win_position_seconds = 0
        # 亏损持仓时间
        self._total_loss_position_seconds = 0

        # 最大连续盈利手数
        self._successive_win_count = 0
        # 最大连续亏损手数
        self._successive_loss_count = 0
        # 最大连续盈利金额
        self._successive_win_value = 0
        # 最大连续亏损金额
        self._successive_loss_value = 0

        # 当前连续盈利手数
        self._current_successive_win_count = 0
        # 当前连续亏损手数
        self._current_successive_loss_count = 0
        # 当前连续盈利金额
        self._current_successive_win_value = 0
        # 当前连续亏损金额
        self._current_successive_loss_value = 0

    def handle_trade(self, event):
        trade = event.trade
        if trade.position_effect == POSITION_EFFECT.OPEN:
            self.handle_open(trade)
        else:
            self.handle_close(trade)

    def handle_open(self, trade):
        order_book_id = trade.order_book_id
        position = {
            # 持仓量
            'quantity': trade.last_quantity,
            # 开仓价
            'price': trade.last_price,
            # datetime
            'dt': trade.datetime
        }

        if trade.side == SIDE.BUY:
            self.buy_positions[order_book_id].append(position)
        else:
            self.sell_positions[order_book_id].append(position)

        self._total_cost += trade.transaction_cost

    def handle_close(self, trade):
        order_book_id = trade.order_book_id
        close_quantity = trade.last_quantity
        close_price = trade.last_price
        while True:
            if close_quantity == 0:
                break
            if trade.side == SIDE.SELL:
                position = self.buy_positions[order_book_id].pop(0)
                if position['quantity'] > close_quantity:
                    trade_quantity = close_quantity
                    close_quantity = 0
                    position['quantity'] = position['quantity'] - close_quantity
                    self.buy_positions[order_book_id].insert(0, position)
                else:
                    trade_quantity = position['quantity']
                    close_quantity = close_quantity - position['quantity']
                pnl = trade_quantity * (close_price - position['price'])
                self._rotary_buy_count += trade_quantity
                self._total_buy_position_seconds += self.cal_seconds(position['dt'], trade.datetime)

                self.cal_stat(pnl, trade_quantity, position['dt'], trade.datetime)
            else:
                position = self.sell_positions[order_book_id].pop(0)
                if position['quantity'] > close_quantity:
                    trade_quantity = close_quantity
                    close_quantity = 0
                    position['quantity'] = position['quantity'] - close_quantity
                    self.sell_positions[order_book_id].insert(0, position)
                else:
                    trade_quantity = position['quantity']
                    close_quantity = close_quantity - position['quantity']
                pnl = trade_quantity * (position['price'] - close_price)
                self._rotary_sell_count += trade_quantity
                self._total_sell_position_seconds += self.cal_seconds(position['dt'], trade.datetime)

                self.cal_stat(pnl, trade_quantity, position['dt'], trade.datetime)

        self._total_cost += trade.transaction_cost

    def cal_stat(self, pnl, trade_quantity, start_dt, end_dt):
        if pnl >= 0:
            # 盈利
            self._total_win_position_seconds += self.cal_seconds(start_dt, end_dt)
            self._rotary_win_count += trade_quantity
            self._total_win_value += pnl
            self._max_win_value = max(pnl / trade_quantity, self._max_win_value)

            self._current_successive_win_count += 1
            self._current_successive_loss_count = 0
            self._current_successive_win_value += pnl
            self._current_successive_loss_value = 0
            self._successive_win_count = max(self._current_successive_win_count, self._successive_win_count)
            self._successive_win_value = max(self._current_successive_win_value, self._successive_win_value)
        else:
            # 亏损
            pnl = abs(pnl)
            self._total_loss_position_seconds += self.cal_seconds(start_dt, end_dt)
            self._rotary_loss_count += trade_quantity
            self._total_loss_value += pnl
            self._max_loss_value = max(pnl / trade_quantity, self._max_loss_value)

            self._current_successive_win_count = 0
            self._current_successive_loss_count += 1
            self._current_successive_win_value = 0
            self._current_successive_loss_value += pnl
            self._successive_loss_count = max(self._current_successive_loss_count, self._successive_loss_count)
            self._successive_loss_value = max(self._current_successive_loss_value, self._successive_loss_value)

    def cal_seconds(self, start, end):
        return (end - start).total_seconds()

    @property
    def rotary_count(self):
        # 回转交易手数
        return self._rotary_buy_count + self._rotary_sell_count

    @property
    def rotary_buy_count(self):
        # 多头回转交易手数
        return self._rotary_buy_count

    @property
    def rotary_sell_count(self):
        # 空头回转交易手数
        return self._rotary_sell_count

    @property
    def rotary_win_count(self):
        # 盈利回转交易手数
        return self._rotary_win_count

    @property
    def rotary_loss_count(self):
        # 亏损回转交易手数
        return self._rotary_loss_count

    @property
    def total_win_value(self):
        # 总盈利金额
        return self._total_win_value

    @property
    def total_loss_value(self):
        # 总亏损金额
        return self._total_loss_value

    @property
    def total_cost(self):
        # 总手续费
        return self._total_cost

    @property
    def win_count_rate(self):
        # 胜率/次数
        return np.nan if self.rotary_count == 0 else self._rotary_win_count / self.rotary_count

    @property
    def win_value_rate(self):
        # 胜率/值
        if self._total_win_value + self._total_loss_value == 0:
            return np.nan
        return self._total_win_value / (self._total_win_value + self._total_loss_value)

    @property
    def cost_pnl_ratio(self):
        # 手续费 / 盈亏
        return np.nan if self.total_pnl == 0 else self._total_cost / self.total_pnl

    @property
    def total_pnl(self):
        # 总盈亏
        return self.total_win_value - self.total_loss_value

    @property
    def average_pnl(self):
        # 平均盈亏
        if self.rotary_count == 0:
            return 0
        return self.total_pnl / self.rotary_count

    @property
    def average_win_value(self):
        # 平均盈利
        if self.rotary_win_count == 0:
            return 0
        return self.total_win_value / self.rotary_win_count

    @property
    def average_loss_value(self):
        # 平均亏损
        if self.rotary_loss_count == 0:
            return 0
        return self.total_loss_value / self.rotary_loss_count

    @property
    def max_win_value(self):
        # 最大盈利金额/每手
        return self._max_win_value

    @property
    def max_loss_value(self):
        # 最大亏损金额/每手
        return self._max_win_value

    @property
    def successive_win_count(self):
        # 最大连续盈利手数
        return self._successive_win_count

    @property
    def successive_loss_count(self):
        # 最大连续亏损手数
        return self._successive_loss_count

    @property
    def successive_win_value(self):
        # 最大连续盈利金额
        return self._successive_win_value

    @property
    def successive_loss_value(self):
        # 最大连续亏损金额
        return self._successive_loss_value

    @property
    def total_position_seconds(self):
        # 总持仓时间
        return self._total_buy_position_seconds + self._total_sell_position_seconds

    @property
    def total_buy_position_seconds(self):
        # 总多头持仓时间
        return self._total_buy_position_seconds

    @property
    def total_sell_position_seconds(self):
        # 总空头持仓时间
        return self._total_sell_position_seconds

    @property
    def total_win_position_seconds(self):
        # 总盈利持仓时间
        return self._total_win_position_seconds

    @property
    def total_loss_position_seconds(self):
        # 总亏损持仓时间
        return self._total_loss_position_seconds

    @property
    def average_position_seconds(self):
        # 平均每手持仓时间
        if self.rotary_count == 0:
            return 0
        return self.total_position_seconds / self.rotary_count

    @property
    def average_buy_position_seconds(self):
        # 平均多头每手持仓时间
        if self._rotary_buy_count == 0:
            return 0
        return self._total_buy_position_seconds / self._rotary_buy_count

    @property
    def average_sell_position_seconds(self):
        # 平均空头每手持仓时间
        if self._rotary_sell_count == 0:
            return 0
        return self._total_sell_position_seconds / self._rotary_sell_count

    @property
    def average_win_position_seconds(self):
        # 平均盈利每手持仓时间
        if self._rotary_win_count == 0:
            return 0
        return self._total_win_position_seconds / self._rotary_win_count

    @property
    def average_loss_position_seconds(self):
        # 平均亏损每手持仓时间
        if self._rotary_loss_count == 0:
            return 0
        return self._total_loss_position_seconds / self._rotary_loss_count

