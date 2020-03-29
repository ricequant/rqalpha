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
from functools import lru_cache
from itertools import chain
from typing import Dict, Iterable, Union, Optional, Type, Callable, List

from rqalpha.const import POSITION_EFFECT
from rqalpha.interface import AbstractAccount
from rqalpha.events import EVENT
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION, INSTRUMENT_TYPE
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.model.order import OrderStyle, Order
from rqalpha.model.trade import Trade
from rqalpha.utils.logger import user_system_log

from .base_position import BasePosition, PositionProxyDict

OrderApiType = Callable[[str, Union[int, float], OrderStyle, bool], List[Order]]
PositionType = Type[BasePosition]


class Account(AbstractAccount):
    """
    账户，多种持仓和现金的集合。

    不同品种的合约持仓可能归属于不同的账户，如股票、转债、场内基金、ETF 期权归属于股票账户，期货、期货期权归属于期货账户
    """

    __abandon_properties__ = [
        "holding_pnl",
        "realized_pnl",
        "dividend_receivable",
    ]

    _position_types = {}  # type: Dict[INSTRUMENT_TYPE, PositionType]

    def __init__(self, type, total_cash, init_positions):
        # type: (str, float, Dict[str, int]) -> None
        self._type = type
        self._total_cash = total_cash  # 包含保证金的总资金

        self._positions = {}
        self._backward_trade_set = set()
        self._frozen_cash = 0

        self.register_event()

        for order_book_id, init_quantity in six.iteritems(init_positions):
            position_direction = POSITION_DIRECTION.LONG if init_quantity > 0 else POSITION_DIRECTION.SHORT
            self._get_or_create_pos(order_book_id, position_direction, init_quantity)

    def __repr__(self):
        positions_repr = {}
        for order_book_id, positions in six.iteritems(self._positions):
            for direction, position in six.iteritems(positions):
                if position.quantity != 0:
                    positions_repr.setdefault(order_book_id, {})[direction.value] = position.quantity
        return "Account(cash={}, total_value={}, positions={})".format(
            self.cash, self.total_value, positions_repr
        )

    @classmethod
    def register_position_type(cls, instrument_type, position_type):
        # type: (INSTRUMENT_TYPE, PositionType) -> None
        # TODO: only can called before instantiated
        cls._position_types[instrument_type] = position_type

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(
            EVENT.TRADE, lambda e: self.apply_trade(e.trade, e.order) if e.account == self else None
        )
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)

        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._on_before_trading)
        event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)

        event_bus.prepend_listener(EVENT.BAR, self._update_last_price)
        event_bus.prepend_listener(EVENT.TICK, self._update_last_price)

    def get_state(self):
        return {
            'positions': {
                order_book_id: {
                    "long": positions[POSITION_DIRECTION.LONG].get_state(),
                    "short": positions[POSITION_DIRECTION.SHORT].get_state()
                } for order_book_id, positions in six.iteritems(self._positions)
            },
            'frozen_cash': self._frozen_cash,
            "total_cash": self._total_cash,
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
        if "total_cash" in state:
            self._total_cash = state["total_cash"]
        else:
            # forward compatible
            total_cash = state["static_total_valueu"]
            for p in self._iter_pos():
                if p._instrument.type == INSTRUMENT_TYPE.FUTURE:
                    continue
                # FIXME: not exactly right
                try:
                    total_cash -= p.equity
                except RuntimeError:
                    total_cash -= p.prev_close * p.quantity

        # forward compatible
        if "dividend_receivable" in state:
            for order_book_id, dividend in six.iteritems(state["dividend_receivable"]):
                self._get_or_create_pos(order_book_id, POSITION_DIRECTION.LONG)._dividend_receivable = (
                    dividend["payable_date"], dividend["quantity"] * dividend["dividend_per_share"]
                )
        if "pending_transform" in state:
            for order_book_id, transform_info in six.iteritems(state["pending_transform"]):
                self._get_or_create_pos(order_book_id, POSITION_DIRECTION.LONG)._pending_transform = transform_info

    def fast_forward(self, orders=None, trades=None):
        if trades:
            close_trades = []
            # 先处理开仓
            for trade in trades:
                if trade.exec_id in self._backward_trade_set:
                    continue
                if trade.position_effect == POSITION_EFFECT.OPEN:
                    self.apply_trade(trade)
                else:
                    close_trades.append(trade)
            # 后处理平仓
            for trade in close_trades:
                self.apply_trade(trade)

        # 计算 Frozen Cash
        if orders:
            self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def get_positions(self):
        # type: () -> Iterable[BasePosition]
        """
        获取所有持仓对象列表，
        """
        return self._iter_pos()

    def get_position(self, order_book_id, direction):
        # type: (str, POSITION_DIRECTION) -> BasePosition
        """
        获取某个标的的持仓对象

        :param order_book_id: 标的编号
        :param direction: 持仓方向

        """
        try:
            return self._positions[order_book_id][direction]
        except KeyError:
            instrument_type = Environment.get_instance().data_proxy.instruments(order_book_id).type
            position_type = self._position_types.get(instrument_type, BasePosition)
            return position_type(order_book_id, direction)

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        return self._get_or_create_pos(order_book_id, position_direction).calc_close_today_amount(trade_amount)

    @property
    def type(self):
        return self._type

    @property
    @lru_cache(None)
    def positions(self):
        return PositionProxyDict(self._positions, self._position_types)

    @property
    def frozen_cash(self):
        # type: () -> float
        """
        冻结资金
        """
        return self._frozen_cash

    @property
    def cash(self):
        # type: () -> float
        """
        可用资金
        """
        return self._total_cash - self.margin - self._frozen_cash

    @property
    def market_value(self):
        # type: () -> float
        """
        [float] 市值
        """
        return sum(p.market_value * (1 if p.direction == POSITION_DIRECTION.LONG else -1) for p in self._iter_pos())

    @property
    def transaction_cost(self):
        # type: () -> float
        """
        总费用
        """
        return sum(p.transaction_cost for p in self._iter_pos())

    @property
    def margin(self):
        # type: () -> float
        """
        总保证金
        """
        return sum(p.margin for p in self._iter_pos())

    @property
    def buy_margin(self):
        # type: () -> float
        """
        多方向保证金
        """
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.LONG))

    @property
    def sell_margin(self):
        # type: () -> float
        """
        空方向保证金
        """
        return sum(p.margin for p in self._iter_pos(POSITION_DIRECTION.SHORT))

    @property
    def daily_pnl(self):
        # type: () -> float
        """
        当日盈亏
        """
        return self.trading_pnl + self.position_pnl - self.transaction_cost

    @property
    def equity(self):
        # type: () -> float
        """
        总权益
        """
        return sum(p.equity for p in self._iter_pos())

    @property
    def total_value(self):
        # type: () -> float
        """
        账户总权益
        """
        return self._total_cash + self.equity

    @property
    def total_cash(self):
        # type: () -> float
        """
        账户总资金
        """
        return self._total_cash - self.margin

    @property
    def position_pnl(self):
        # type: () -> float
        """
        昨仓盈亏
        """
        return sum(p.position_pnl for p in self._iter_pos())

    @property
    def trading_pnl(self):
        # type: () -> float
        """
        交易盈亏
        """
        return sum(p.trading_pnl for p in self._iter_pos())

    def position_validator_enabled(self, order_book_id):  # type: (str) -> bool
        return self._get_or_create_pos(order_book_id, POSITION_DIRECTION.LONG).position_validator_enabled

    def _on_before_trading(self, _):
        trading_date = Environment.get_instance().trading_dt.date()
        for position in self._iter_pos():
            self._total_cash += position.before_trading(trading_date)

    def _on_settlement(self, _):
        trading_date = Environment.get_instance().trading_dt.date()

        for order_book_id, positions in list(six.iteritems(self._positions)):
            for position in six.itervalues(positions):
                delta_cash = position.settlement(trading_date)
                self._total_cash += delta_cash

        for order_book_id, positions in list(six.iteritems(self._positions)):
            if all(p.quantity == 0 for p in six.itervalues(positions)):
                del self._positions[order_book_id]

        self._backward_trade_set.clear()

        # 如果 total_value <= 0 则认为已爆仓，清空仓位，资金归0
        forced_liquidation = Environment.get_instance().config.base.forced_liquidation
        if self.total_value <= 0 and forced_liquidation:
            if self._positions:
                user_system_log.warn(_("Trigger Forced Liquidation, current total_value is 0"))
            self._positions.clear()
            self._total_cash = 0

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

    def apply_trade(self, trade, order=None):
        # type: (Trade, Optional[Order]) -> None
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        if trade.position_effect == POSITION_EFFECT.MATCH:
            self._total_cash += self._get_or_create_pos(order_book_id, POSITION_DIRECTION.LONG).apply_trade(trade)
            self._total_cash += self._get_or_create_pos(order_book_id, POSITION_DIRECTION.SHORT).apply_trade(trade)
        else:
            self._total_cash += self._get_or_create_pos(order_book_id, trade.position_direction).apply_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
        if order and trade.position_effect != POSITION_EFFECT.MATCH:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * self._frozen_cash_of_order(order)
            else:
                self._frozen_cash -= self._frozen_cash_of_order(order)

    def _iter_pos(self, direction=None):
        # type: (Optional[POSITION_DIRECTION]) -> Iterable[BasePosition]
        if direction:
            return (p[direction] for p in six.itervalues(self._positions))
        else:
            return chain(*[six.itervalues(p) for p in six.itervalues(self._positions)])

    def _get_or_create_pos(self, order_book_id, direction, init_quantity=0):
        # type: (str, Union[str, POSITION_DIRECTION], Optional[int]) -> BasePosition
        if order_book_id not in self._positions:
            instrument_type = Environment.get_instance().data_proxy.instruments(order_book_id).type
            position_type = self._position_types.get(instrument_type, BasePosition)
            if direction == POSITION_DIRECTION.LONG:
                long_init_position, short_init_position = init_quantity, 0
            else:
                long_init_position, short_init_position = 0, init_quantity

            positions = self._positions.setdefault(order_book_id, {
                POSITION_DIRECTION.LONG: position_type(order_book_id, POSITION_DIRECTION.LONG, long_init_position),
                POSITION_DIRECTION.SHORT: position_type(order_book_id, POSITION_DIRECTION.SHORT, short_init_position)
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
            instrument = env.data_proxy.instruments(order.order_book_id)
            order_cost = instrument.calc_cash_occupation(order.frozen_price, order.quantity, order.position_direction)
        else:
            order_cost = 0
        return order_cost + env.get_order_transaction_cost(order)

    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
