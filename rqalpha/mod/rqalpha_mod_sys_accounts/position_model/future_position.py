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

from rqalpha.environment import Environment
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, SIDE, POSITION_EFFECT

from .asset_position import AssetPositionProxy


class FuturePositionProxy(AssetPositionProxy):

    __abandon_properties__ = AssetPositionProxy.__abandon_properties__ +[
        "holding_pnl",
        "buy_holding_pnl",
        "sell_holding_pnl",
        "realized_pnl",
        "buy_realized_pnl",
        "sell_realized_pnl",
        "buy_avg_holding_price",
        "sell_avg_holding_price"
    ]

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE.name

    def set_state(self, state):
        assert self.order_book_id == state['order_book_id']
        if "long" in state and "short" in state:
            super(FuturePositionProxy, self).set_state(state)
        else:
            # for compatible
            buy_old_quantity = buy_logical_old_quantity = sum(q for _, q in state.get("buy_old_holding_list", []))
            self._long.set_state({
                "old_quantity": buy_old_quantity,
                "logical_old_quantity": buy_logical_old_quantity,
                "today_quantity": sum(q for _, q in state.get("buy_today_holding_list", [])),
                "avg_price": state.get("buy_avg_open_price"),
                "trade_cost": 0,
                "transaction_cost": state.get("buy_transaction_cost")
            })

            sell_old_quantity = sell_logical_old_quantity = sum(q for _, q in state.get("sell_old_holding_list", []))
            self._short.set_state({
                "old_quantity": sell_old_quantity,
                "logical_old_quantity": sell_logical_old_quantity,
                "today_quantity": sum(q for _, q in state.get("sell_today_holding_list", [])),
                "avg_price": state.get("sell_avg_open_price"),
                "trade_cost": 0,
                "transaction_cost": state.get("sell_transaction_cost")
            })

    @property
    def margin_rate(self):
        return self._long.margin_rate

    @property
    def contract_multiplier(self):
        return self._long.contract_multiplier

    @property
    def buy_market_value(self):
        """
        [float] 多方向市值
        """
        return self._long.market_value

    @property
    def sell_market_value(self):
        """
        [float] 空方向市值
        """
        return self._short.market_value

    @property
    def buy_position_pnl(self):
        """
        [float] 多方向昨仓盈亏
        """
        return self._long.position_pnl

    @property
    def sell_position_pnl(self):
        """
        [float] 空方向昨仓盈亏
        """
        return self._short.position_pnl

    @property
    def buy_trading_pnl(self):
        """
        [float] 多方向交易盈亏
        """
        return self._long.trading_pnl

    @property
    def sell_trading_pnl(self):
        """
        [float] 空方向交易盈亏
        """
        return self._short.trading_pnl

    @property
    def buy_daily_pnl(self):
        """
        [float] 多方向每日盈亏
        """
        return self.buy_position_pnl + self.buy_trading_pnl

    @property
    def sell_daily_pnl(self):
        """
        [float] 空方向每日盈亏
        """
        return self.sell_position_pnl + self.sell_trading_pnl

    @property
    def buy_pnl(self):
        """
        [float] 买方向累计盈亏
        """
        return self._long.pnl

    @property
    def sell_pnl(self):
        """
        [float] 空方向累计盈亏
        """
        return self._short.pnl

    @property
    def buy_old_quantity(self):
        """
        [int] 多方向昨仓
        """
        return self._long.old_quantity

    @property
    def sell_old_quantity(self):
        """
        [int] 空方向昨仓
        """
        return self._short.old_quantity

    @property
    def buy_today_quantity(self):
        """
        [int] 多方向今仓
        """
        return self._long.today_quantity

    @property
    def sell_today_quantity(self):
        """
        [int] 空方向今仓
        """
        return self._short.today_quantity

    @property
    def buy_quantity(self):
        """
        [int] 多方向持仓
        """
        return self.buy_old_quantity + self.buy_today_quantity

    @property
    def sell_quantity(self):
        """
        [int] 空方向持仓
        """
        return self.sell_old_quantity + self.sell_today_quantity

    @property
    def buy_margin(self):
        """
        [float] 多方向持仓保证金
        """
        return self._long.margin

    @property
    def sell_margin(self):
        """
        [float] 空方向持仓保证金
        """
        return self._short.margin

    @property
    def buy_avg_open_price(self):
        """
        [float] 多方向平均开仓价格
        """
        return self._long.avg_price

    @property
    def sell_avg_open_price(self):
        """
        [float] 空方向平均开仓价格
        """
        return self._short.avg_price

    @property
    def buy_transaction_cost(self):
        """
        [float] 多方向交易费率
        """
        return self._long.transaction_cost

    @property
    def sell_transaction_cost(self):
        """
        [float] 空方向交易费率
        """
        return self._short.transaction_cost

    @property
    def closable_today_sell_quantity(self):
        buy_close_today_order_quantity = sum(o.unfilled_quantity for o in self.open_orders if o.side == SIDE.BUY and
                                             o.position_effect == POSITION_EFFECT.CLOSE_TODAY)
        return self.sell_today_quantity - buy_close_today_order_quantity

    @property
    def closable_today_buy_quantity(self):
        sell_close_today_order_quantity = sum(o.unfilled_quantity for o in self.open_orders if o.side == SIDE.SELL and
                                              o.position_effect == POSITION_EFFECT.CLOSE_TODAY)
        return self.buy_today_quantity - sell_close_today_order_quantity

    @property
    def closable_buy_quantity(self):
        """
        [float] 可平多方向持仓
        """
        sell_close_order_quantity = sum(o.unfilled_quantity for o in self.open_orders if o.side == SIDE.SELL and
                                        o.position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY))
        return self.buy_quantity - sell_close_order_quantity

    @property
    def closable_sell_quantity(self):
        """
        [float] 可平空方向持仓
        """
        buy_close_order_quantity = sum(o.unfilled_quantity for o in self.open_orders if o.side == SIDE.BUY and
                                       o.position_effect in (POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY))
        return self.sell_quantity - buy_close_order_quantity

    def is_de_listed(self):
        """
        判断合约是否过期
        """
        instrument = Environment.get_instance().get_instrument(self.order_book_id)
        current_date = Environment.get_instance().trading_dt
        if instrument.de_listed_date is not None and current_date >= instrument.de_listed_date:
            return True
        return False

    def cal_close_today_amount(self, trade_amount, trade_side):
        if trade_side == SIDE.SELL:
            close_today_amount = trade_amount - self.buy_old_quantity
        else:
            close_today_amount = trade_amount - self.sell_old_quantity
        return max(close_today_amount, 0)

    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    buy_holding_pnl = deprecated_property("buy_holding_pnl", "buy_position_pnl")
    sell_holding_pnl = deprecated_property("sell_holding_pnl", "sell_position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
    buy_realized_pnl = deprecated_property("buy_realized_pnl", "buy_trading_pnl")
    sell_realized_pnl = deprecated_property("sell_realized_pnl", "sell_trading_pnl")
    buy_avg_holding_price = deprecated_property("buy_avg_holding_price", "buy_avg_open_price")
    sell_avg_holding_price = deprecated_property("sell_avg_holding_price", "sell_avg_open_price")
