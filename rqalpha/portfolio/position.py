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

from collections import UserDict
from datetime import date
from typing import Dict, Iterable, Tuple, Optional

from rqalpha.const import POSITION_DIRECTION, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.interface import AbstractPosition
from rqalpha.model.instrument import Instrument
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.utils import is_valid_price
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import PropertyReprMeta, property_repr


def new_position_meta():
    type_map = {}

    class Meta(PropertyReprMeta):
        def __new__(mcs, *args, **kwargs):
            cls = super(Meta, mcs).__new__(mcs, *args, **kwargs)
            try:
                instrument_types = cls.__instrument_types__
            except AttributeError:
                pass
            else:
                for instrument_type in instrument_types:
                    type_map[instrument_type] = cls
            return cls

    return type_map, Meta


POSITION_TYPE_MAP, PositionMeta = new_position_meta()
POSITION_PROXY_TYPE_MAP, PositionProxyMeta = new_position_meta()


class Position(AbstractPosition, metaclass=PositionMeta):
    __repr_properties__ = (
        "order_book_id", "direction", "quantity", "market_value", "trading_pnl", "position_pnl", "last_price"
    )

    # 用于注册该 Position 类型适用的 instrument_type
    __instrument_types__ = []

    def __new__(cls, order_book_id, direction, init_quantity=0, init_price=None):
        if cls == Position:
            ins_type = Environment.get_instance().data_proxy.instrument(order_book_id).type
            try:
                position_cls = POSITION_TYPE_MAP[ins_type]
            except KeyError:
                raise NotImplementedError("")
            return position_cls.__new__(position_cls, order_book_id, direction, init_quantity, init_price)
        else:
            return object.__new__(cls)

    def __init__(self, order_book_id, direction, init_quantity=0, init_price=None):
        self._env = Environment.get_instance()

        self._order_book_id = order_book_id
        self._instrument = self._env.data_proxy.instrument(order_book_id)  # type: Instrument
        self._direction = direction

        self._quantity = init_quantity
        self._old_quantity = init_quantity
        self._logical_old_quantity = 0

        self._avg_price: float = init_price or 0
        self._trade_cost: float = 0
        self._transaction_cost: float = 0
        self._prev_close: Optional[float] = init_price
        self._last_price: Optional[float] = init_price

        self._direction_factor = 1 if direction == POSITION_DIRECTION.LONG else -1

    @property
    def order_book_id(self):
        # type: () -> str
        return self._order_book_id

    @property
    def direction(self):
        # type: () -> POSITION_DIRECTION
        return self._direction

    @property
    def quantity(self):
        # type: () -> int
        return self._quantity

    @property
    def transaction_cost(self):
        # type: () -> float
        return self._transaction_cost

    @property
    def avg_price(self):
        # type: () -> float
        return self._avg_price

    @property
    def trading_pnl(self):
        # type: () -> float
        trade_quantity = self._quantity - self._logical_old_quantity
        return (trade_quantity * self.last_price - self._trade_cost) * self._direction_factor

    @property
    def position_pnl(self):
        # type: () -> float
        return self._logical_old_quantity * (self.last_price - self.prev_close) * self._direction_factor

    @property
    def pnl(self):
        # type: () -> float
        """
        返回该持仓的累积盈亏
        """
        return (self.last_price - self.avg_price) * self._quantity * self._direction_factor

    @property
    def market_value(self):
        # type: () -> float
        return self.last_price * self._quantity if self._quantity else 0

    @property
    def equity(self):
        # type: () -> float
        return self.last_price * self._quantity if self._quantity else 0

    @property
    def prev_close(self):
        if not is_valid_price(self._prev_close):
            env = Environment.get_instance()
            self._prev_close = env.data_proxy.get_prev_close(self._order_book_id, env.trading_dt)
        return self._prev_close

    @property
    def last_price(self):
        if not self._last_price:
            env = Environment.get_instance()
            self._last_price = env.data_proxy.get_last_price(self._order_book_id)
            if not is_valid_price(self._last_price):
                raise RuntimeError(_("invalid price of {order_book_id}: {price}").format(
                    order_book_id=self._order_book_id, price=self._last_price
                ))
        return self._last_price

    @property
    def closable(self):
        # type: () -> int
        """
        可平仓位
        """
        order_quantity = sum(o.unfilled_quantity for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        return self._quantity - order_quantity

    @property
    def today_closable(self):
        # type: () -> int
        return self._quantity - self._old_quantity - sum(
            o.unfilled_quantity for o in self._open_orders if o.position_effect == POSITION_EFFECT.CLOSE_TODAY
        )

    def get_state(self):
        """"""
        return {
            "old_quantity": self._old_quantity,
            "logical_old_quantity": self._logical_old_quantity,
            "quantity": self._quantity,
            "avg_price": self._avg_price,
            "trade_cost": self._trade_cost,
            "transaction_cost": self._transaction_cost,
            "prev_close": self._prev_close
        }

    def set_state(self, state):
        """"""
        self._old_quantity = state.get("old_quantity", 0)
        self._logical_old_quantity = state.get("logical_old_quantity", self._old_quantity)
        if "quantity" in state:
            self._quantity = state["quantity"]
        else:
            # forward compatible
            self._quantity = self._old_quantity + state.get("today_quantity", 0)
        self._avg_price = state.get("avg_price", 0)
        self._trade_cost = state.get("trade_cost", 0)
        self._transaction_cost = state.get("transaction_cost", 0)
        self._prev_close = state.get("prev_close")

    def before_trading(self, trading_date):
        # type: (date) -> float
        # 返回该阶段导致总资金的变化量
        self._prev_close = self.last_price
        self._transaction_cost = 0
        return 0

    def apply_trade(self, trade):
        # type: (Trade) -> float
        # 返回总资金的变化量
        self._transaction_cost += trade.transaction_cost
        if trade.position_effect == POSITION_EFFECT.OPEN:
            if self._quantity < 0:
                self._avg_price = trade.last_price if self._quantity + trade.last_quantity > 0 else 0
            else:
                cost = self._quantity * self._avg_price + trade.last_quantity * trade.last_price
                self._avg_price = cost / (self._quantity + trade.last_quantity)
            self._quantity += trade.last_quantity
            self._trade_cost += trade.last_price * trade.last_quantity
            return (-1 * trade.last_price * trade.last_quantity) - trade.transaction_cost
        elif trade.position_effect == POSITION_EFFECT.CLOSE:
            # 先平昨，后平今
            self._old_quantity -= min(trade.last_quantity, self._old_quantity)
            self._quantity -= trade.last_quantity
            self._trade_cost -= trade.last_price * trade.last_quantity
            return trade.last_price * trade.last_quantity - trade.transaction_cost
        else:
            raise NotImplementedError("{} does not support position effect {}".format(
                self.__class__.__name__, trade.position_effect
            ))

    def settlement(self, trading_date):
        # type: (date) -> float
        # 返回该阶段导致总资金的变化量以及反映该阶段引起其他持仓变化的虚拟交易，虚拟交易用于换代码，转股等操作
        self._old_quantity = self._quantity
        self._logical_old_quantity = self._old_quantity
        self._trade_cost = self._non_closable = 0
        return 0

    def update_last_price(self, price):
        self._last_price = price

    def calc_close_today_amount(self, trade_amount):
        return 0

    @property
    def _open_orders(self):
        # type: () -> Iterable[Order]
        for order in Environment.get_instance().broker.get_open_orders(self.order_book_id):
            if order.position_direction == self._direction:
                yield order


class PositionProxy(metaclass=PositionProxyMeta):
    __repr_properties__ = (
        "order_book_id", "positions"
    )
    # 用于注册该 Position 类型适用的 instrument_type
    __instrument_types__ = []

    def __init__(self, long, short):
        # type: (Position, Position) -> PositionProxy
        self._long = long
        self._short = short

    __repr__ = property_repr

    @property
    def type(self):
        raise NotImplementedError

    @property
    def order_book_id(self):
        return self._long.order_book_id

    @property
    def last_price(self):
        return self._long.last_price

    @property
    def market_value(self):
        return self._long.market_value - self._short.market_value

    # -- PNL 相关
    @property
    def position_pnl(self):
        """
        [float] 昨仓盈亏，当前交易日盈亏中来源于昨仓的部分

        多方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (最新价 - 昨收价)
        空方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (昨收价 - 最新价)

        """
        return self._long.position_pnl + self._short.position_pnl

    @property
    def trading_pnl(self):
        """
        [float] 交易盈亏，当前交易日盈亏中来源于当日成交的部分

        单比买方向成交的交易盈亏 = 成交量 * (最新价 - 成交价)
        单比卖方向成交的交易盈亏 = 成交量 * (成交价 - 最新价)

        """
        return self._long.trading_pnl + self._short.trading_pnl

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏

        当日盈亏 = 昨仓盈亏 + 交易盈亏

        """
        return self._long.position_pnl + self._long.trading_pnl + self._short.position_pnl + \
               self._short.trading_pnl - self.transaction_cost

    @property
    def pnl(self):
        return self._long.pnl + self._short.pnl

    # -- Quantity 相关
    @property
    def open_orders(self):
        return Environment.get_instance().broker.get_open_orders(self.order_book_id)

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 保证金

        保证金 = 持仓量 * 最新价 * 合约乘数 * 保证金率

        股票保证金 = 市值 = 持仓量 * 最新价

        """
        return self._long.margin + self._short.margin

    @property
    def transaction_cost(self):
        """
        [float] 交易费率
        """
        return self._long.transaction_cost + self._short.transaction_cost

    @property
    def positions(self):
        return [self._long, self._short]

    @property
    def long(self):
        return self._long

    @property
    def short(self):
        return self._short


PositionDictType = Dict[str, Dict[POSITION_DIRECTION, Position]]


class PositionProxyDict(UserDict):
    def __init__(self, positions):
        super(PositionProxyDict, self).__init__()
        self._positions = positions  # type: PositionDictType

    def keys(self):
        return self._positions.keys()

    def __getitem__(self, order_book_id):
        position_type, position_proxy_type = self._get_position_types(order_book_id)
        if order_book_id not in self._positions:
            long = position_type(order_book_id, POSITION_DIRECTION.LONG)
            short = position_type(order_book_id, POSITION_DIRECTION.SHORT)
        else:
            positions = self._positions[order_book_id]
            long = positions[POSITION_DIRECTION.LONG]
            short = positions[POSITION_DIRECTION.SHORT]
        return position_proxy_type(long, short)

    def __contains__(self, item):
        return item in self._positions

    def __iter__(self):
        return iter(self._positions)

    def __len__(self):
        return len(self._positions)

    def __setitem__(self, key, value):
        raise TypeError("{} object does not support item assignment".format(self.__class__.__name__))

    def __delitem__(self, key):
        raise TypeError("{} object does not support item deletion".format(self.__class__.__name__))

    def __repr__(self):
        return repr({k: self[k] for k in self._positions.keys()})

    def _get_position_types(self, order_book_id):
        # type: (str) -> Tuple[type, type]
        instrument_type = Environment.get_instance().data_proxy.instrument(order_book_id).type
        position_type = POSITION_TYPE_MAP.get(instrument_type, Position)
        position_proxy_type = POSITION_PROXY_TYPE_MAP.get(instrument_type, PositionProxy)
        return position_type, position_proxy_type
