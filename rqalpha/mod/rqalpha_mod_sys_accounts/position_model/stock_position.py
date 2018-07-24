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
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, SIDE
from rqalpha.environment import Environment
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log


class StockPosition(BasePosition):

    __abandon_properties__ = [
        "bought_quantity",
        "sold_quantity",
        "bought_value",
        "sold_value",
        "average_cost"
    ]
    stock_t1 = True

    def __init__(self, order_book_id):
        super(StockPosition, self).__init__(order_book_id)
        self._quantity = 0
        self._avg_price = 0
        self._non_closable = 0     # 当天买入的不能卖出
        self._frozen = 0            # 冻结量
        self._transaction_cost = 0  # 交易费用

    def __repr__(self):
        return 'StockPosition({})'.format(self.__dict__)

    def get_state(self):
        return {
            'order_book_id': self._order_book_id,
            'quantity': self._quantity,
            'avg_price': self._avg_price,
            'non_closable': self._non_closable,
            'frozen': self._frozen,
            'transaction_cost': self._transaction_cost,
        }

    def set_state(self, state):
        assert self._order_book_id == state['order_book_id']
        self._quantity = state['quantity']
        self._avg_price = state['avg_price']
        self._non_closable = state['non_closable']
        self._frozen = state['frozen']
        self._transaction_cost = state['transaction_cost']

    def apply_trade(self, trade):
        self._transaction_cost += trade.transaction_cost
        if trade.side == SIDE.BUY:
            # 对应卖空情况
            if self._quantity < 0:
                if trade.last_quantity <= -1 * self._quantity:
                    self._avg_price = 0
                else:
                    self._avg_price = trade.last_price
            else:
                self._avg_price = (self._avg_price * self._quantity + trade.last_quantity * trade.last_price) / (
                    self._quantity + trade.last_quantity)
            self._quantity += trade.last_quantity
            if self.stock_t1 and self._order_book_id not in {'510900.XSHG', '513030.XSHG', '513100.XSHG', '513500.XSHG'}:
                # 除了上述 T+0 基金，其他都是 T+1
                self._non_closable += trade.last_quantity
        else:
            self._quantity -= trade.last_quantity
            self._frozen -= trade.last_quantity

    def apply_settlement(self):
        self._non_closable = 0

    def reset_frozen(self, frozen):
        self._frozen = frozen

    def cal_close_today_amount(self, *args):
        return 0

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK.name

    def split_(self, ratio):
        self._quantity *= ratio
        # split 发生时，这两个值理论上应该都是0
        self._frozen *= ratio
        self._non_closable *= ratio
        self._avg_price /= ratio

    def dividend_(self, dividend_per_share):
        self._avg_price -= dividend_per_share

    def on_order_pending_new_(self, order):
        if order.side == SIDE.SELL:
            self._frozen += order.quantity

    def on_order_creation_reject_(self, order):
        if order.side == SIDE.SELL:
            self._frozen -= order.quantity

    def on_order_cancel_(self, order):
        if order.side == SIDE.SELL:
            self._frozen -= order.unfilled_quantity

    @property
    def quantity(self):
        """
        [int] 当前持仓股数
        """
        return self._quantity

    @property
    def avg_price(self):
        """
        [float] 获得该持仓的买入均价，计算方法为每次买入的数量做加权平均
        """
        return self._avg_price

    @property
    def pnl(self):
        return self._quantity * (self.last_price - self._avg_price)

    @property
    def sellable(self):
        """
        [int] 该仓位可卖出股数。T＋1的市场中sellable = 所有持仓 - 今日买入的仓位 - 已冻结
        """
        return self._quantity - self._non_closable - self._frozen

    @property
    def market_value(self):
        return self._quantity * self.last_price

    @property
    def transaction_cost(self):
        return self._transaction_cost

    @property
    def value_percent(self):
        """
        [float] 获得该持仓的实时市场价值在股票投资组合价值中所占比例，取值范围[0, 1]
        """
        accounts = Environment.get_instance().portfolio.accounts
        if DEFAULT_ACCOUNT_TYPE.STOCK.name not in accounts:
            return 0
        total_value = accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name].total_value
        return 0 if total_value == 0 else self.market_value / total_value

    # -- Function
    def is_de_listed(self):
        """
        判断合约是否过期
        """
        env = Environment.get_instance()
        instrument = env.get_instrument(self._order_book_id)
        current_date = env.trading_dt

        if instrument.de_listed_date is not None:
            if instrument.de_listed_date.date() > env.config.base.end_date:
                return False
            if current_date >= env.data_proxy.get_previous_trading_date(instrument.de_listed_date):
                return True
        return False

    # ------------------------------------ Abandon Property ------------------------------------

    @property
    def bought_quantity(self):
        """
        [已弃用]
        """
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('stock_position.bought_quantity'))
        return self._quantity

    @property
    def sold_quantity(self):
        """
        [已弃用]
        """
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('stock_position.sold_quantity'))
        return 0

    @property
    def bought_value(self):
        """
        [已弃用]
        """
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('stock_position.bought_value'))
        return self._quantity * self._avg_price

    @property
    def sold_value(self):
        """
        [已弃用]
        """
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('stock_position.sold_value'))
        return 0

    @property
    def average_cost(self):
        """
        [已弃用] 请使用 avg_price 获取持仓买入均价
        """
        user_system_log.warn(_(u"[abandon] {} is no longer valid.").format('stock_position.average_cost'))
        return self._avg_price
