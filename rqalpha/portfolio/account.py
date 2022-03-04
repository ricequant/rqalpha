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

from itertools import chain
from typing import Callable, Dict, Iterable, List, Optional, Union, Tuple

import six
from rqalpha.const import POSITION_DIRECTION, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT
from rqalpha.model.order import Order, OrderStyle
from rqalpha.model.trade import Trade
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
from rqalpha.portfolio.position import Position, PositionProxyDict

OrderApiType = Callable[[str, Union[int, float], OrderStyle, bool], List[Order]]


class AccountMeta(type):
    def __new__(mcs, *args, **kwargs):
        cls = type.__new__(mcs, *args, **kwargs)
        cls._margin = cls.margin
        cls.margin = property(lambda s: 0)  # black magic: improve performance for pure stock strategy
        return cls


class Account(metaclass=AccountMeta):
    """
    账户，多种持仓和现金的集合。

    不同品种的合约持仓可能归属于不同的账户，如股票、转债、场内基金、ETF 期权归属于股票账户，期货、期货期权归属于期货账户
    """

    __abandon_properties__ = [
        "holding_pnl",
        "realized_pnl",
        "dividend_receivable",
    ]

    def __init__(self, account_type: str, total_cash: float, init_positions: Dict[str, Tuple[int, Optional[float]]]):
        self._type = account_type
        self._total_cash = total_cash  # 包含保证金的总资金

        self._positions = {}
        self._backward_trade_set = set()
        self._frozen_cash = 0

        self.register_event()

        self._management_fee_calculator_func = lambda account, rate: account.total_value * rate
        self._management_fee_rate = 0.0
        self._management_fees = 0.0

        for order_book_id, (init_quantity, init_price) in init_positions.items():
            position_direction = POSITION_DIRECTION.LONG if init_quantity > 0 else POSITION_DIRECTION.SHORT
            self._get_or_create_pos(order_book_id, position_direction, init_quantity, init_price)

    def __repr__(self):
        positions_repr = {}
        for order_book_id, positions in self._positions.items():
            for direction, position in positions.items():
                if position.quantity != 0:
                    positions_repr.setdefault(order_book_id, {})[direction.value] = position.quantity
        return "Account(cash={}, total_value={}, positions={})".format(
            self.cash, self.total_value, positions_repr
        )

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
                    POSITION_DIRECTION.LONG: positions[POSITION_DIRECTION.LONG].get_state(),
                    POSITION_DIRECTION.SHORT: positions[POSITION_DIRECTION.SHORT].get_state()
                } for order_book_id, positions in self._positions.items()
            },
            'frozen_cash': self._frozen_cash,
            "total_cash": self._total_cash,
            'backward_trade_set': list(self._backward_trade_set),
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])
        self._total_cash = state["total_cash"]

        self._positions.clear()
        for order_book_id, positions_state in state['positions'].items():
            for direction in POSITION_DIRECTION:
                position = self._get_or_create_pos(order_book_id, direction)
                if direction in positions_state.keys():
                    position.set_state(positions_state[direction])
                else:
                    position.set_state(positions_state[direction.lower()])

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
            self._frozen_cash = sum(
                order.unfilled_quantity * order.quantity / order.init_frozen_cash for order in orders if
                order.is_active())

    def get_positions(self):
        # type: () -> Iterable[Position]
        """
        获取所有持仓对象列表，
        """
        for position in self._iter_pos():
            if position.quantity == 0 and position.equity == 0:
                continue
            yield position

    def get_position(self, order_book_id: str, direction: POSITION_DIRECTION = POSITION_DIRECTION.LONG) -> Position:
        """
        获取某个标的的持仓对象

        :param order_book_id: 标的编号
        :param direction: 持仓方向
        """
        try:
            return self._positions[order_book_id][direction]
        except KeyError:
            return Position(order_book_id, direction)

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction):
        return self._get_or_create_pos(order_book_id, position_direction).calc_close_today_amount(trade_amount)

    @property
    def type(self):
        return self._type

    @property
    @lru_cache(None)
    def positions(self):
        return PositionProxyDict(self._positions)

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
    def margin(self) -> float:
        """
        总保证金
        """
        return sum(getattr(p, "margin", 0) for p in self._iter_pos())

    @property
    def buy_margin(self):
        # type: () -> float
        """
        多方向保证金
        """
        return sum(getattr(p, "margin", 0) for p in self._iter_pos(POSITION_DIRECTION.LONG))

    @property
    def sell_margin(self):
        # type: () -> float
        """
        空方向保证金
        """
        return sum(getattr(p, "margin", 0) for p in self._iter_pos(POSITION_DIRECTION.SHORT))

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
        持仓总权益
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

    def _on_before_trading(self, _):
        trading_date = Environment.get_instance().trading_dt.date()
        for position in self._iter_pos():
            self._total_cash += position.before_trading(trading_date)

    def _on_settlement(self, event):
        trading_date = Environment.get_instance().trading_dt.date()

        for order_book_id, positions in list(self._positions.items()):
            for position in six.itervalues(positions):
                delta_cash = position.settlement(trading_date)
                self._total_cash += delta_cash

        for order_book_id, positions in list(self._positions.items()):
            if all(p.quantity == 0 and p.equity == 0 for p in six.itervalues(positions)):
                del self._positions[order_book_id]

        self._backward_trade_set.clear()

        fee = self._management_fee()
        self._management_fees += fee
        self._total_cash -= fee

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
        order.set_frozen_cash(self._frozen_cash_of_order(order))
        self._frozen_cash += order.init_frozen_cash

    def _on_order_unsolicited_update(self, event):
        if event.account != self:
            return
        order = event.order
        if order.filled_quantity != 0:
            self._frozen_cash -= order.unfilled_quantity / order.quantity * order.init_frozen_cash
        else:
            self._frozen_cash -= order.init_frozen_cash

    def apply_trade(self, trade, order=None):
        # type: (Trade, Optional[Order]) -> None
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        if order and trade.position_effect != POSITION_EFFECT.MATCH:
            if trade.last_quantity != order.quantity:
                self._frozen_cash -= trade.last_quantity / order.quantity * order.init_frozen_cash
            else:
                self._frozen_cash -= order.init_frozen_cash
        if trade.position_effect == POSITION_EFFECT.MATCH:
            delta_cash = self._get_or_create_pos(
                order_book_id, POSITION_DIRECTION.LONG
            ).apply_trade(trade) + self._get_or_create_pos(
                order_book_id, POSITION_DIRECTION.SHORT
            ).apply_trade(trade)
            self._total_cash += delta_cash
        else:
            delta_cash = self._get_or_create_pos(order_book_id, trade.position_direction).apply_trade(trade)
            self._total_cash += delta_cash
        self._backward_trade_set.add(trade.exec_id)

    def _iter_pos(self, direction=None):
        # type: (Optional[POSITION_DIRECTION]) -> Iterable[Position]
        if direction:
            return (p[direction] for p in six.itervalues(self._positions))
        else:
            return chain(*[six.itervalues(p) for p in six.itervalues(self._positions)])

    def _get_or_create_pos(
            self,
            order_book_id: str,
            direction: Union[POSITION_DIRECTION, str],
            init_quantity: float = 0,
            init_price : Optional[float] = None
    ) -> Position:
        if order_book_id not in self._positions:
            env = Environment.get_instance()
            if direction == POSITION_DIRECTION.LONG:
                long_quantity, short_quantity = init_quantity, 0
            else:
                long_quantity, short_quantity = 0, init_quantity
            positions = self._positions.setdefault(order_book_id, {
                POSITION_DIRECTION.LONG: Position(order_book_id, POSITION_DIRECTION.LONG, long_quantity, init_price),
                POSITION_DIRECTION.SHORT: Position(order_book_id, POSITION_DIRECTION.SHORT, short_quantity, init_price)
            })
            if not init_price:
                last_price = env.get_last_price(order_book_id)
                for p in positions.values():
                    p.update_last_price(last_price)
            if hasattr(positions[direction], "margin") and hasattr(self.__class__, "_margin"):
                # black magic: improve performance for pure stock strategy
                setattr(self.__class__, "margin", self.__class__._margin)
                del self.__class__._margin
        else:
            positions = self._positions[order_book_id]
        return positions[direction]

    def _update_last_price(self, _):
        env = Environment.get_instance()
        for order_book_id, positions in self._positions.items():
            price = env.get_last_price(order_book_id)
            if price == price:
                for position in six.itervalues(positions):
                    position.update_last_price(price)

    def _frozen_cash_of_order(self, order):
        env = Environment.get_instance()
        if order.position_effect == POSITION_EFFECT.OPEN:
            instrument = env.data_proxy.instrument(order.order_book_id)
            order_cost = instrument.calc_cash_occupation(order.frozen_price, order.quantity, order.position_direction)
        else:
            order_cost = 0
        return order_cost + env.get_order_transaction_cost(order)

    def _management_fee(self):
        # type: () -> float
        """计算账户管理费用"""
        if self._management_fee_rate == 0:
            return 0
        fee = self._management_fee_calculator_func(self, self._management_fee_rate)
        return fee

    def register_management_fee_calculator(self, calculator):
        # type: (Callable[[Account, float], float]) -> None
        """
        设置管理费用计算逻辑
        该方法需要传入一个函数

        .. code-block:: python

        def management_fee_calculator(account, rate):
            return len(account.positions) * rate

        def init(context):
            context.portfolio.accounts["STOCK"].set_management_fee_calculator(management_fee_calculator)

        """
        self._management_fee_calculator_func = calculator

    def set_management_fee_rate(self, rate):
        # type: (float) -> None
        """管理费用计算费率"""
        self._management_fee_rate = rate

    @property
    def management_fees(self):
        # type: () -> float
        """该账户的管理费用总计"""
        return self._management_fees

    def deposit_withdraw(self, amount):
        # type: (float) -> None
        """出入金"""
        if (amount < 0) and (self.cash < amount * -1):
            raise ValueError(_('insufficient cash, current {}, target withdrawal {}').format(self._total_cash, amount))
        self._total_cash += amount

    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
