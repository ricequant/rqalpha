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

from rqalpha.interface import AbstractAccount
from rqalpha.utils.repr import property_repr
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log


class BaseAccount(AbstractAccount):

    __abandon_properties__ = [
        "portfolio_value",
        "starting_cash",
        "daily_returns",
        "total_returns",
        "pnl"
    ]

    AGGRESSIVE_UPDATE_LAST_PRICE = False

    __repr__ = property_repr

    def __init__(self, total_cash, positions, backward_trade_set=set(), register_event=True):
        self._positions = positions
        self._frozen_cash = 0
        self._total_cash = total_cash
        self._backward_trade_set = backward_trade_set
        self._transaction_cost = 0
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
        return self._transaction_cost

    # ------------------------------------ Abandon Property ------------------------------------

    @property
    def portfolio_value(self):
        """
        [已弃用] 请使用 total_value
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('account.portfolio_value'))
        return self.total_value

    @property
    def starting_cash(self):
        """
        [已弃用] 请使用 total_value
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('account.starting_cash'))
        return 0

    @property
    def daily_returns(self):
        """
        [已弃用] 请使用 total_value
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('account.daily_returns'))
        return 0

    @property
    def total_returns(self):
        """
        [已弃用] 请使用 total_value
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('account.total_returns'))
        return 0

    @property
    def pnl(self):
        """
        [已弃用] 请使用 total_value
        """
        user_system_log.warn(_(u"[abandon] {} is no longer used.").format('account.pnl'))
        return 0
