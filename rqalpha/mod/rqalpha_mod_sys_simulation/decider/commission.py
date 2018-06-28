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

import abc
from six import with_metaclass
from collections import defaultdict

from rqalpha.const import HEDGE_TYPE, COMMISSION_TYPE, POSITION_EFFECT, SIDE
from rqalpha.environment import Environment


class BaseCommission(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_commission(self, trade):
        raise NotImplementedError


class StockCommission(BaseCommission):
    def __init__(self, multiplier, min_commission):
        self.rate = 0.0008
        self.multiplier = multiplier
        self.commission_map = defaultdict(lambda: min_commission)
        self.min_commission = min_commission

    def get_commission(self, trade):
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
        order_book_id = trade.order_book_id
        env = Environment.get_instance()
        if env.data_proxy.instruments(order_book_id).type == 'PublicFund':
            if trade.side == SIDE.BUY:
                rate = env.data_proxy.public_fund_commission(order_book_id, True)
                rate = rate / (1 + rate)
            else:
                rate = env.data_proxy.public_fund_commission(order_book_id, False)
            cost_money = trade.last_price * trade.last_quantity * rate * self.multiplier
            return cost_money
        commission = self.commission_map[order_id]
        cost_money = trade.last_price * trade.last_quantity * self.rate * self.multiplier
        if cost_money > commission:
            if commission == self.min_commission:
                self.commission_map[order_id] = 0
                return cost_money
            else:
                self.commission_map[order_id] = 0
                return cost_money - commission
        else:
            if commission == self.min_commission:
                self.commission_map[order_id] -= cost_money
                return commission
            else:
                self.commission_map[order_id] -= cost_money
                return 0


class FutureCommission(BaseCommission):
    def __init__(self, multiplier, hedge_type=HEDGE_TYPE.SPECULATION):
        """
        期货目前不计算最小手续费
        """
        self.multiplier = multiplier
        self.hedge_type = hedge_type

    def get_commission(self, trade):
        order_book_id = trade.order_book_id
        env = Environment.get_instance()
        info = env.data_proxy.get_commission_info(order_book_id)
        commission = 0
        if info['commission_type'] == COMMISSION_TYPE.BY_MONEY:
            contract_multiplier = env.get_instrument(trade.order_book_id).contract_multiplier
            if trade.position_effect == POSITION_EFFECT.OPEN:
                commission += trade.last_price * trade.last_quantity * contract_multiplier * info['open_commission_ratio']
            else:
                commission += trade.last_price * (trade.last_quantity - trade.close_today_amount) * contract_multiplier * info[
                    'close_commission_ratio']
                commission += trade.last_price * trade.close_today_amount * contract_multiplier * info[
                    'close_commission_today_ratio']
        else:
            if trade.position_effect == POSITION_EFFECT.OPEN:
                commission += trade.last_quantity * info['open_commission_ratio']
            else:
                commission += (trade.last_quantity - trade.close_today_amount) * info['close_commission_ratio']
                commission += trade.close_today_amount * info['close_commission_today_ratio']
        return commission * self.multiplier
