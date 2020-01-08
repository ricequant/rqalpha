# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import six
from itertools import chain
from typing import Dict, Iterable, Union, Optional

from rqalpha.const import POSITION_EFFECT
from rqalpha.interface import AbstractAccount
from rqalpha.utils.repr import property_repr
from rqalpha.events import EVENT
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION

from .asset_position import AssetPosition
from .order import Order
from .trade import Trade


class AssetAccount(AbstractAccount):

    __repr__ = property_repr

    enable_position_validator = True

    def __init__(self, total_cash, positions=None, backward_trade_set=None):
        # type: (float, Dict[str, Dict[POSITION_DIRECTION, AssetPosition]], set) -> None
        self._static_total_value = total_cash
        self._positions = positions or {}
        self._backward_trade_set = backward_trade_set or set()
        self._frozen_cash = 0

        self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(
            EVENT.TRADE, lambda e: self._apply_trade(e.trade, e.order) if e.account == self else None
        )
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)

        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._on_before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, lambda e: self.apply_settlement())

        event_bus.add_listener(EVENT.BAR, self._update_last_price)
        event_bus.add_listener(EVENT.TICK, self._update_last_price)

    def get_state(self):
        return {
            'positions': {
                order_book_id: {
                    "long": positions[POSITION_DIRECTION.LONG].get_state(),
                    "short": positions[POSITION_DIRECTION.SHORT].get_state()
                } for order_book_id, positions in six.iteritems(self._positions)
            },
            'frozen_cash': self._frozen_cash,
            'static_total_value': self._static_total_value,
            'backward_trade_set': list(self._backward_trade_set),
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])

        self._positions.clear()
        for order_book_id, positions_state in six.iteritems(state['positions']):
            for direction in POSITION_DIRECTION:
                state = positions_state[direction]
                position = self._get_or_create_pos(order_book_id, direction)
                position.set_state(state)

        if "static_total_value" in state:
            self._static_total_value = state["static_total_value"]
        else:
            static_total_value = state["total_cash"]
            for p in self._iter_pos():
                try:
                    static_total_value += (p.margin - (p.trading_pnl + p.position_pnl) + p.transaction_cost)
                except RuntimeError:
                    # 新老结构切换之间发生退市的
                    static_total_value += p.margin
                    self._positions.pop(p.order_book_id)
            self._static_total_value = state["total_cash"] + self.margin - self.daily_pnl + self.transaction_cost

    def fast_forward(self, orders=None, trades=None):
        if trades:
            close_trades = []
            # 先处理开仓
            for trade in trades:
                if trade.exec_id in self._backward_trade_set:
                    continue
                if trade.position_effect == POSITION_EFFECT.OPEN:
                    self._apply_trade(trade)
                else:
                    close_trades.append(trade)
            # 后处理平仓
            for trade in close_trades:
                self._apply_trade(trade)

        # 计算 Frozen Cash
        if orders:
            self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def get_positions(self):
        # type: () -> Iterable[AssetPosition]
        return self._iter_pos()

    def get_position(self, order_book_id, direction):
        # type: (str, POSITION_DIRECTION) -> AssetPosition
        try:
            return self._positions[order_book_id][direction]
        except KeyError:
            return AssetPosition(order_book_id, direction)

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        raise NotImplementedError

    def order(self, order_book_id, quantity, style, target=False):
        raise NotImplementedError

    @property
    def positions(self):
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError

    def apply_settlement(self):
        raise NotImplementedError

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

        可用资金 = 总资金 - 冻结资金

        """
        return self.total_cash - self._frozen_cash

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(p.market_value * (1 if p.direction == POSITION_DIRECTION.LONG else -1) for p in self._iter_pos())

    @property
    def transaction_cost(self):
        """
        [float] 总费用
        """
        return sum(p.transaction_cost for p in self._iter_pos())

    @property
    def margin(self):
        """
        [float] 总保证金
        """
        return sum(p.margin for p in self._iter_pos())

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.trading_pnl + self.position_pnl - self.transaction_cost

    @property
    def total_value(self):
        """
        [float] 账户总权益

        期货账户总权益 = 期货昨日总权益 + 当日盈亏

        """
        return self._static_total_value + self.daily_pnl

    @property
    def total_cash(self):
        """
        [float] 账户总资金

        期货账户总资金会受保证金变化的影响变化，期货账户总资金 = 总权益 - 保证金

        """
        return self._static_total_value + self.daily_pnl - self.margin

    @property
    def position_pnl(self):
        """
        [float] 昨仓盈亏
        """
        return sum(p.position_pnl for p in self._iter_pos())

    @property
    def trading_pnl(self):
        """
        [float] 交易盈亏
        """
        return sum(p.trading_pnl for p in self._iter_pos())

    @property
    def position_validator_enabled(self):  # type: () -> bool
        return self.enable_position_validator

    def _on_before_trading(self, event):
        raise NotImplementedError

    def _on_order_pending_new(self, event):
        if event.account != self:
            return
        order = event.order
        self._frozen_cash += self._frozen_cash_of_order(order)

    def _on_order_unsolicited_update(self, event):
        if event.account != self:
            return
        order = event.order
        if order.filled_quantity != 0:
            self._frozen_cash -= order.unfilled_quantity / order.quantity * self._frozen_cash_of_order(order)
        else:
            self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _apply_trade(self, trade, order=None):
        # type: (Trade, Optional[Order]) -> None
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        if trade.position_effect == POSITION_EFFECT.MATCH:
            self._get_or_create_pos(order_book_id, POSITION_DIRECTION.LONG).apply_trade(trade)
            self._get_or_create_pos(order_book_id, POSITION_DIRECTION.SHORT).apply_trade(trade)
        else:
            self._get_or_create_pos(order_book_id, trade.position_direction).apply_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
        if order:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * self._frozen_cash_of_order(order)
            else:
                self._frozen_cash -= self._frozen_cash_of_order(order)

    def _iter_pos(self, direction=None):
        # type: (Optional[POSITION_DIRECTION]) -> Iterable[AssetPosition]
        if direction:
            return (p[direction] for p in six.itervalues(self._positions))
        else:
            return chain(*[six.itervalues(p) for p in six.itervalues(self._positions)])

    def _get_or_create_pos(self, order_book_id, direction):
        # type: (str, Union[str, POSITION_DIRECTION]) -> AssetPosition
        if order_book_id not in self._positions:
            positions = self._positions.setdefault(order_book_id, {
                POSITION_DIRECTION.LONG: AssetPosition(order_book_id, POSITION_DIRECTION.LONG),
                POSITION_DIRECTION.SHORT: AssetPosition(order_book_id, POSITION_DIRECTION.SHORT)
            })
        else:
            positions = self._positions[order_book_id]
        return positions[direction]

    def _update_last_price(self, _):
        env = Environment.get_instance()
        for order_book_id, positions in six.iteritems(self._positions):
            price = env.get_last_price(order_book_id)
            if price == price:
                for position in six.itervalues(positions):
                    position.update_last_price(price)

    def _frozen_cash_of_order(self, order):
        env = Environment.get_instance()
        if order.position_effect == POSITION_EFFECT.OPEN:
            order_cost = env.data_proxy.instruments(order.order_book_id).calc_margin(order.frozen_price, order.quantity)
        else:
            order_cost = 0
        return order_cost + env.get_order_transaction_cost(self.type, order)
