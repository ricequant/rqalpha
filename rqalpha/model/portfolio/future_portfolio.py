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

from .base_portfolio import BasePortfolio
from ..dividend import Dividend
from ..position import Positions, PositionsClone, FuturePosition
from ...utils.repr import dict_repr
from ...execution_context import ExecutionContext


FuturePersistMap = {
    "_yesterday_portfolio_value": "_yesterday_portfolio_value",
    "_yesterday_units": "_yesterday_units",
    "_cash": "_cash",
    "_starting_cash": "_starting_cash",
    "_units": "_units",
    "_start_date": "_start_date",
    "_current_date": "_current_date",
    "_frozen_cash": "_frozen_cash",
    "_total_commission": "_total_commission",
    "_total_tax": "_total_tax",
    "_dividend_receivable": "_dividend_receivable",
    "_dividend_info": "_dividend_info",
    "_daily_transaction_cost": "_daily_transaction_cost",
    "_positions": "_positions",
}


class FuturePortfolioClone(object):
    __repr__ = dict_repr


class FuturePortfolio(BasePortfolio):
    def __init__(self, cash, start_date, account_type):
        super(FuturePortfolio, self).__init__(cash, start_date, account_type)
        self._positions = Positions(FuturePosition)
        self._portfolio_value = None

    @classmethod
    def from_recovery(cls, account, start_date, start_cash, account_type, portfolio_dict, orders, trades):
        """
        portfolio_dict = {
            'yesterday_portfolio_value': None,
            'units': None,
            'yesterday_units': None,
            'positions': []
        }
        """
        portfolio = cls(start_cash, start_date, account_type)

        portfolio._units = portfolio_dict['units']
        portfolio._yesterday_units = portfolio_dict['yesterday_units']
        portfolio._yesterday_portfolio_value = portfolio_dict['yesterday_portfolio_value']

        trades_dict = {}
        orders_dict = {}

        for order in orders:
            if order.order_book_id not in orders_dict:
                orders_dict[order.order_book_id] = []
            orders_dict[order.order_book_id].append(order)

        for trade in trades:
            order = trade.order
            if order.order_book_id not in trades_dict:
                trades_dict[order.order_book_id] = []
            trades_dict[order.order_book_id].append(trade)

        order_book_id_set = set(orders_dict.keys())
        order_book_id_set.update(trades_dict.keys())
        order_book_id_set.update(portfolio_dict['positions'].keys())

        for order_book_id in order_book_id_set:
            orders = orders_dict[order_book_id] if order_book_id in orders_dict else []
            trades = trades_dict[order_book_id] if order_book_id in trades_dict else []
            position_dict = portfolio_dict['positions'][order_book_id] if order_book_id in portfolio_dict['positions'] else {}
            position = FuturePosition.from_recovery(order_book_id, position_dict, trades)
            portfolio._positions[order_book_id] = position

            for order in orders:
                value = order._frozen_price * order.unfilled_quantity * position._contract_multiplier
                portfolio._frozen_cash += ExecutionContext.cal_margin(order_book_id, order.side, value)

        portfolio._cash = portfolio.yesterday_unit_net_value * portfolio.units - portfolio._frozen_cash - portfolio.margin

        return portfolio

    def restore_from_dict_(self, portfolio_dict):
        self._cash = portfolio_dict['_cash']
        self._start_date = portfolio_dict['_start_date']
        self._positions.clear()
        self._dividend_info.clear()
        for persist_key, origin_key in six.iteritems(FuturePersistMap):
            if persist_key == "_dividend_info":
                for order_book_id, dividend_dict in six.iteritems(portfolio_dict[persist_key]):
                    self._dividend_info[order_book_id] = Dividend.__from_dict__(dividend_dict)
            elif persist_key == "_positions":
                for order_book_id, position_dict in six.iteritems(portfolio_dict[persist_key]):
                    self._positions[order_book_id] = FuturePosition.__from_dict__(position_dict)
            else:
                try:
                    setattr(self, origin_key, portfolio_dict[persist_key])
                except KeyError as e:
                    if persist_key in ["_yesterday_units", "_units"]:
                        # FIXME 对于已有 persist_key 做暂时error handling 处理。
                        setattr(self, origin_key, portfolio_dict["_starting_cash"])
                    else:
                        raise e

    def __to_dict__(self):
        p_dict = {}
        for persist_key, origin_key in six.iteritems(FuturePersistMap):
            if persist_key == "_dividend_info":
                p_dict[persist_key] = {oid: dividend.__to_dict__() for oid, dividend in six.iteritems(getattr(self, origin_key))}
            elif persist_key == "_positions":
                p_dict[persist_key] = {oid: position.__to_dict__() for oid, position in six.iteritems(getattr(self, origin_key))}
            else:
                p_dict[persist_key] = getattr(self, origin_key)
        return p_dict

    @property
    def positions(self):
        """
        【dict】一个包含期货子组合仓位的字典，以order_book_id作为键，position对象作为值
        """
        return self._positions

    @property
    def cash(self):
        """
        【float】可用资金
        """
        return self.portfolio_value - self.margin - self.daily_holding_pnl - self.frozen_cash

    @property
    def portfolio_value(self):
        """
        【float】总权益，昨日总权益+当日盈亏
        """
        if self._portfolio_value is None:
            # self._portfolio_value = self._cash + self._frozen_cash + self.daily_holding_pnl + self.margin
            self._portfolio_value = self.yesterday_unit_net_value * self.units + self.daily_pnl

        return self._portfolio_value

    # @property
    # def _risk_cash(self):
    #     # 风控资金
    #     risk_cash = self.cash if self.daily_holding_pnl > 0 else self.cash + self.daily_holding_pnl
    #     return risk_cash

    @property
    def buy_margin(self):
        """
        【float】多头保证金
        """
        # 买保证金
        # TODO 这里需要考虑 T TF 这种跨合约单向大边的情况
        # TODO 这里需要考虑 同一个合约跨期单向大边的情况
        return sum(position.buy_margin for position in six.itervalues(self.positions))

    @property
    def sell_margin(self):
        """
        【float】空头保证金
        """
        # 卖保证金
        return sum(position.sell_margin for position in six.itervalues(self.positions))

    @property
    def margin(self):
        """
        【float】已占用保证金
        """
        # 总保证金
        return sum(position.margin for position in six.itervalues(self.positions))

    @property
    def daily_holding_pnl(self):
        """
        【float】当日浮动盈亏
        """
        # 当日持仓盈亏
        return sum(position.daily_holding_pnl for position in six.itervalues(self.positions))

    @property
    def daily_realized_pnl(self):
        """
        【float】当日平仓盈亏
        """
        # 当日平仓盈亏
        return sum(position.daily_realized_pnl for position in six.itervalues(self.positions))

    @property
    def daily_pnl(self):
        """
        【float】当日盈亏，当日浮动盈亏 + 当日平仓盈亏 - 当日费用
        """
        # 当日盈亏
        return self.daily_realized_pnl + self.daily_holding_pnl - self.transaction_cost

    def _clone(self):
        p = FuturePortfolioClone()
        for key in dir(self):
            if "__" in key:
                continue
            if key == "positions":
                ps = PositionsClone(FuturePosition)
                for order_book_id in self.positions:
                    ps[order_book_id] = self.positions[order_book_id]._clone()
                setattr(p, key, ps)
            else:
                setattr(p, key, getattr(self, key))
        return p

