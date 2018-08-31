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

from collections import defaultdict

from rqalpha.interface import AbstractTransactionCostDecider
from rqalpha.environment import Environment
from rqalpha.const import SIDE, HEDGE_TYPE, COMMISSION_TYPE, POSITION_EFFECT


class StockTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_rate, commission_multiplier, min_commission):
        self.commission_rate = commission_rate
        self.commission_multiplier = commission_multiplier
        self.commission_map = defaultdict(lambda: min_commission)
        self.min_commission = min_commission

        self.env = Environment.get_instance()

    def _get_public_fund_commission(self, order_book_id, side, cost_money):
        if side == SIDE.BUY:
            rate = self.env.data_proxy.public_fund_commission(order_book_id, True)
            rate = rate / (1 + rate)
        else:
            rate = self.env.data_proxy.public_fund_commission(order_book_id, False)
        return cost_money * rate * self.commission_multiplier

    def _get_order_commission(self, order_book_id, side, price, quantity):
        if self.env.data_proxy.instruments(order_book_id).type == 'PublicFund':
            return self._get_public_fund_commission(order_book_id, side, price * quantity)
        commission = price * quantity * self.commission_rate * self.commission_multiplier
        return max(commission, self.min_commission)

    def _get_tax(self, order_book_id, side, cost_money):
        raise NotImplementedError

    def get_trade_commission(self, trade):
        """
        计算手续费这个逻辑比较复杂，按照如下算法来计算：
        1.  定义一个剩余手续费的概念，根据order_id存储在commission_map中，默认为min_commission
        2.  当trade来时计算该trade产生的手续费cost_money
        3.  如果cost_money > commission
            3.1 如果commission 等于 min_commission，说明这是第一笔trade，此时，直接commission置0，返回cost_money即可
            3.2 如果commission 不等于 min_commission, 则说明这不是第一笔trade,此时，直接cost_money - commission即可
        4.  如果cost_money <= commission
            4.1 如果commission 等于 min_commission, 说明是第一笔trade, 此时，返回min_commission(提前把最小手续费收了)
            4.2 如果commission 不等于 min_commission， 说明不是第一笔trade, 之前的trade中min_commission已经收过了，所以返回0.
        """
        order_id = trade.order_id
        if self.env.data_proxy.instruments(trade.order_book_id).type == 'PublicFund':
            return self._get_public_fund_commission(trade.order_book_id, trade.side, trade.last_price * trade.last_quantity)
        commission = self.commission_map[order_id]
        cost_commission = trade.last_price * trade.last_quantity * self.commission_rate * self.commission_multiplier
        if cost_commission > commission:
            if commission == self.min_commission:
                self.commission_map[order_id] = 0
                return cost_commission
            else:
                self.commission_map[order_id] = 0
                return cost_commission - commission
        else:
            if commission == self.min_commission:
                self.commission_map[order_id] -= cost_commission
                return commission
            else:
                self.commission_map[order_id] -= cost_commission
                return 0

    def get_trade_tax(self, trade):
        return self._get_tax(trade.order_book_id, trade.side, trade.last_price * trade.last_quantity)

    def get_order_transaction_cost(self, order):
        order_price = order.price if order.price else self.env.get_last_price(order.order_book_id)
        commission = self._get_order_commission(order.order_book_id, order.side, order_price, order.quantity)
        tax = self._get_tax(order.order_book_id, order.side, order_price * order.quantity)
        return tax + commission


class CNStockTransactionCostDecider(StockTransactionCostDecider):
    def __init__(self, commission_multiplier, min_commission):
        super(CNStockTransactionCostDecider, self).__init__(0.0008, commission_multiplier, min_commission)
        self.tax_rate = 0.001

    def _get_tax(self, order_book_id, side, cost_money):
        instrument = Environment.get_instance().get_instrument(order_book_id)
        if instrument.type != 'CS':
            return 0
        return cost_money * self.tax_rate if side == SIDE.SELL else 0


class HKStockTransactionCostDecider(StockTransactionCostDecider):
    def __init__(self, commission_multiplier, min_commission):
        super(HKStockTransactionCostDecider, self).__init__(0.0005, commission_multiplier, min_commission)
        self.tax_rate = 0.0011

    def _get_tax(self, order_book_id, _, cost_money):
        """
        港交所收费项目繁多，按照如下逻辑计算税费：
        1. 税费比例为 0.11%，不足 1 元按 1 元记，四舍五入保留两位小数（包括印花税、交易征费、交易系统使用费）。
        2，五元固定费用（包括卖方收取的转手纸印花税、买方收取的过户费用）。
        """
        instrument = Environment.get_instance().get_instrument(order_book_id)
        if instrument.type != 'CS':
            return 0
        tax = cost_money * self.tax_rate
        if tax < 1:
            tax = 1
        else:
            tax = round(tax, 2)
        return tax + 5


class CNFutureTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_multiplier):
        self.commission_multiplier = commission_multiplier
        self.hedge_type = HEDGE_TYPE.SPECULATION

        self.env = Environment.get_instance()

    def _get_commission(self, order_book_id, position_effect, price, quantity, close_today_quantity):
        info = self.env.data_proxy.get_commission_info(order_book_id)
        commission = 0
        if info['commission_type'] == COMMISSION_TYPE.BY_MONEY:
            contract_multiplier = self.env.get_instrument(order_book_id).contract_multiplier
            if position_effect == POSITION_EFFECT.OPEN:
                commission += price * quantity * contract_multiplier * info[
                    'open_commission_ratio']
            else:
                commission += price * (
                        quantity - close_today_quantity
                ) * contract_multiplier * info['close_commission_ratio']
                commission += price * close_today_quantity * contract_multiplier * info['close_commission_today_ratio']
        else:
            if position_effect == POSITION_EFFECT.OPEN:
                commission += quantity * info['open_commission_ratio']
            else:
                commission += (quantity - close_today_quantity) * info['close_commission_ratio']
                commission += close_today_quantity * info['close_commission_today_ratio']
        return commission * self.commission_multiplier

    def get_trade_commission(self, trade):
        return self._get_commission(
            trade.order_book_id, trade.position_effect, trade.last_price, trade.last_quantity, trade.close_today_amount
        )

    def get_trade_tax(self, trade):
        return 0

    def get_order_transaction_cost(self, order):
        order_price = order.price if order.price else self.env.get_last_price(order.order_book_id)

        close_today_quantity = order.quantity if order.position_effect == POSITION_EFFECT.CLOSE_TODAY else 0

        return self._get_commission(
            order.order_book_id, order.position_effect, order_price, order.quantity, close_today_quantity
        )

