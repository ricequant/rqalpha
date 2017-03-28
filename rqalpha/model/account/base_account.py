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


class BaseAccount(object):
    def __init__(self, total_cash, positions, backward_trade_set=set(), register_event=True):
        self._positions = positions
        self._frozen_cash = 0
        self._total_cash = total_cash
        self._backward_trade_set = backward_trade_set
        if register_event:
            self.register_event()

    def register_event(self):
        """
        注册事件
        """
        raise NotImplementedError

    def fast_forward(self, orders, trades=list()):
        """
        同步账户信息至最新状态
        :param orders: 订单列表，主要用来计算frozen_cash，如果为None则不计算frozen_cash
        :param trades: 交易列表，基于Trades 将当前Positions ==> 最新Positions
        """
        raise NotImplementedError

    @property
    def type(self):
        """
        [enum] 账户类型
        """
        raise NotImplementedError

    @property
    def total_value(self):
        """
        [float]总权益
        """
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def set_state(self, state):
        raise NotImplementedError

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        return self._positions

    @property
    def frozen_cash(self):
        """
        [float] 冻结资金
        """
        return self._frozen_cash

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return self._total_cash - self._frozen_cash

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(position.market_value for position in six.itervalues(self._positions))

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(position.transaction_cost for position in six.itervalues(self._positions))

