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
from datetime import date
from typing import Optional, Deque
from collections import deque
from functools import cached_property

from decimal import Decimal
from numpy import ndarray

from rqalpha.interface import TransactionCost
from rqalpha.model.trade import Trade
from rqalpha.const import POSITION_DIRECTION, SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE, INSTRUMENT_TYPE
from rqalpha.environment import Environment
from rqalpha.portfolio.position import Position, PositionProxy
from rqalpha.data.data_proxy import DataProxy
from rqalpha.utils import INST_TYPE_IN_STOCK_ACCOUNT, is_valid_price
from rqalpha.utils.datetime_func import convert_date_to_date_int
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.class_helper import deprecated_property
from rqalpha.utils.i18n import gettext as _
from rqalpha.core.events import EVENT, Event


def _int_to_date(d):
    r, d = divmod(d, 100)
    y, m = divmod(r, 100)
    return date(year=y, month=m, day=d)


class StockPosition(Position):
    # 注意，涉及到非人民币的持仓：
    #   1. before_trading 和 settlement 返回的资金变化为本币
    #   2. 命名带 local 后缀的 property 返回的值为本币计价
    #   3. 其他 property 返回的值应为结算货币计价
    __repr_properties__ = (
        "order_book_id", "direction", "quantity", "market_value", "trading_pnl", "position_pnl", "last_price"
    )
    __instrument_types__ = INST_TYPE_IN_STOCK_ACCOUNT

    dividend_reinvestment = False
    dividend_tax_rate: float = 0.
    cash_return_by_stock_delisted = True
    t_plus_enabled = True

    def __init__(self, order_book_id, direction, init_quantity=0, init_price=None):
        super(StockPosition, self).__init__(order_book_id, direction, init_quantity, init_price)
        self._dividend_receivable: Deque[tuple[date, float]] = deque()
        self._pending_transform = None
        self._non_closable = 0

        # 当日发生的拆分和分红，用于 position_pnl 的计算
        self._daily_dividend: float = 0.
        self._daily_split: float = 1.
        self._unadjusted_prev_close = None

    @property
    def unadjusted_prev_close(self) -> float:
        if self._unadjusted_prev_close is None:
            self._unadjusted_prev_close = self._env.data_proxy.get_prev_close(self._order_book_id, self._env.trading_dt, "none")
        return self._unadjusted_prev_close

    @property
    def dividend_receivable(self):
        # type: () -> float
        """
        应收分红
        """
        return sum(v for _, v in self._dividend_receivable)

    @property
    def equity(self):
        # type: () -> float
        """
        持仓权益
        """
        return super(StockPosition, self).equity + self.dividend_receivable

    @property
    def market_value_local(self):
        return self.market_value

    @property
    def trading_pnl(self) -> float:
        trade_quantity = self._quantity - self._logical_old_quantity * self._daily_split
        return (trade_quantity * self.last_price - self._trade_cost) * self._direction_factor

    @property
    def position_pnl(self) -> float:
        if not self._logical_old_quantity:
            # 新股第一天，没有 prev_close
            return 0
        return (self._logical_old_quantity * self._daily_split * (
            self.last_price - self.unadjusted_prev_close / self._daily_split
        ) + self._daily_dividend) * self._direction_factor

    @property
    def closable(self):
        # type: () -> int
        order_quantity = sum(o.unfilled_quantity for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        if self.t_plus_enabled:
            return self._quantity - order_quantity - self._non_closable
        return self._quantity - order_quantity

    def set_state(self, state):
        super(StockPosition, self).set_state(state)
        self._dividend_receivable = state.get("dividend_receivable")
        self._pending_transform = state.get("pending_transform")
        self._non_closable = state.get("non_closable", 0)

    def get_state(self):
        state = super(StockPosition, self).get_state()
        state.update({
            "dividend_receivable": self._dividend_receivable,
            "pending_transform": self._pending_transform,
            "non_closable": self._non_closable
        })
        return state

    def before_trading(self, trading_date):
        # type: (date) -> float
        delta_cash = super(StockPosition, self).before_trading(trading_date)
        self._unadjusted_prev_close = self.last_price
        if self._quantity == 0 and not self._dividend_receivable:
            return delta_cash
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        data_proxy = self._env.data_proxy
        self._daily_dividend = self._handle_dividend_book_closure(trading_date, data_proxy)
        delta_cash += self._handle_dividend_payable(trading_date)
        self._daily_split = self._handle_split(trading_date, data_proxy)
        return delta_cash

    def apply_trade(self, trade):
        # type: (Trade) -> float
        # 返回总资金的变化量
        delta_cash = super(StockPosition, self).apply_trade(trade)
        if trade.position_effect == POSITION_EFFECT.OPEN and self._market_tplus >= 1:  # type: ignore
            self._non_closable += trade.last_quantity
        return delta_cash

    def settlement(self, trading_date):
        # type: (date) -> float
        super(StockPosition, self).settlement(trading_date)

        if self._quantity == 0:
            return 0
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        next_date = self._env.data_proxy.get_next_trading_date(trading_date)
        instrument = self._env.data_proxy.instrument_not_none(self._order_book_id)
        delta_cash = 0
        if instrument.de_listed_at(next_date):
            try:
                transform_data = self._env.data_proxy.get_share_transformation(self._order_book_id)
            except NotImplementedError:
                pass
            else:
                if transform_data is not None:
                    successor, conversion_ratio = transform_data
                    self._env.portfolio.get_account(successor).apply_trade(Trade.__from_create__(
                        order_id=None,
                        price=self.avg_price / conversion_ratio,
                        amount=self._quantity * conversion_ratio,
                        side=SIDE.BUY,
                        position_effect=POSITION_EFFECT.OPEN,
                        order_book_id=successor,
                        transaction_cost=TransactionCost.zero()
                    ))
                    for direction in POSITION_DIRECTION:
                        successor_position = self._env.portfolio.get_position(successor, direction)
                        successor_position.update_last_price(self._last_price / conversion_ratio)
                    # 把购买 successor 消耗的 cash 补充回来
                    delta_cash = self.market_value_local
            if self.cash_return_by_stock_delisted:
                delta_cash = self.market_value_local
                self._trade_cost = -self.market_value  # 相当于卖掉了，所以给一个负成本
            self._quantity = self._old_quantity = 0
            self._queue.clear()
        return delta_cash

    @cached_property
    def _market_tplus(self):
        return self._instrument.market_tplus

    @cached_property
    def _all_dividends(self) -> ndarray | None:
        dividends = self._env.data_proxy.get_dividend(self._order_book_id)
        return dividends

    @cached_property
    def _all_splits(self) -> ndarray | None:
        splits = self._env.data_proxy.get_split(self._order_book_id)
        if splits is None:
            return None
        splits = splits.copy()
        splits["ex_date"] = splits["ex_date"] // 1000000
        return splits

    def _get_dividends_or_splits(self, events: ndarray | None, trading_date: date, date_field: str):
        if events is None:
            return None
        last_date = self._env.data_proxy.get_previous_trading_date(trading_date)
        last_date_int = convert_date_to_date_int(last_date)
        today_int = convert_date_to_date_int(trading_date)
        events_dates = events[date_field]
        left_pos = events_dates.searchsorted(last_date_int, side="right")
        right_pos = events_dates.searchsorted(today_int, side="right")
        events = events[left_pos: right_pos]
        return events
        
    def _handle_dividend_book_closure(self, trading_date: date, data_proxy: DataProxy) -> float:
        dividends = self._get_dividends_or_splits(self._all_dividends, trading_date, "ex_dividend_date")  # type: ignore[reportIncompatibleVariableOverride]
        if dividends is None or len(dividends) == 0:
            return 0
        dividend_per_share: float = (dividends["dividend_cash_before_tax"] / dividends["round_lot"]).sum() * (1 - self.dividend_tax_rate)
        self._avg_price -= dividend_per_share
        # 前一天结算发生了除息, 此时 last_price 还是前一个交易日的收盘价，需要改为 除息后收盘价, 否则影响在before_trading中查看盈亏
        self._last_price -= dividend_per_share  # type: ignore
        
        # FIXME: 这里隐含了获取的多条 dividend 的 payable_date 都相同的假设
        payable_date = _int_to_date(dividends["payable_date"][-1])
        self._dividend_receivable.append((payable_date, self._quantity * dividend_per_share))
        return self._quantity * dividend_per_share

    def _handle_dividend_payable(self, trading_date: date) -> float:
        # 返回总资金的变化量
        if not self._dividend_receivable:
            return 0
        payable_value = 0.
        while self._dividend_receivable and self._dividend_receivable[0][0] <= trading_date:
            _, dividend_value = self._dividend_receivable.popleft()            
            payable_value += dividend_value
        if payable_value and self.dividend_reinvestment:
            last_price = self.last_price
            amount = int(Decimal(payable_value) / Decimal(last_price))
            round_lot = self._instrument.round_lot
            amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
            if amount > 0:
                account = self._env.get_account(self._order_book_id)
                trade = Trade.__from_create__(
                    None, last_price, amount, SIDE.BUY, POSITION_EFFECT.OPEN, self._order_book_id,
                )
                self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=None))
            return payable_value - amount * last_price
        else:
            return payable_value

    def _handle_split(self, trading_date, data_proxy) -> float:
        splits = self._get_dividends_or_splits(self._all_splits, trading_date, "ex_date")  # type: ignore[reportIncompatibleVariableOverride]
        if splits is None or len(splits) == 0:
            return 1.
        ratio: float = splits["split_factor"].cumprod()[-1]
        self._avg_price /= ratio
        self._last_price /= ratio  # type: ignore
        ratio_decimal = Decimal(ratio)
        # int(6000 * 1.15) -> 6899
        self._old_quantity = self._quantity = round(Decimal(self._quantity) * ratio_decimal)
        self._queue.handle_split(ratio_decimal, self._quantity)
        return ratio


class FuturePosition(Position):
    __repr_properties__ = (
        "order_book_id", "direction", "old_quantity", "quantity", "margin", "market_value", "trading_pnl",
        "position_pnl", "last_price"
    )
    __instrument_types__ = [INSTRUMENT_TYPE.FUTURE]

    old_quantity = property(lambda self: self._old_quantity)
    today_quantity = property(lambda self: self._quantity - self._old_quantity)

    @cached_property
    def contract_multiplier(self):
        return self._instrument.contract_multiplier
    
    @property
    def margin_rate(self):
        # type: () -> float
        if self.direction == POSITION_DIRECTION.LONG:
            margin_ratio = self._instrument.get_long_margin_ratio(self._env.trading_dt.date())
        elif self.direction == POSITION_DIRECTION.SHORT:
            margin_ratio = self._instrument.get_short_margin_ratio(self._env.trading_dt.date())
        return margin_ratio * self._env.config.base.margin_multiplier

    @property
    def equity(self):
        # type: () -> float
        """"""
        return self._quantity * (self.last_price - self._avg_price) * self.contract_multiplier * self._direction_factor

    @property
    def margin(self):
        # rtpe: () -> float
        """
        保证金 = 持仓量 * 最新价 * 合约乘数 * 保证金率
        """
        return self.margin_rate * self.market_value

    @property
    def market_value(self):
        # type: () -> float
        return self.contract_multiplier * super(FuturePosition, self).market_value

    @property
    def trading_pnl(self):
        # type: () -> float
        return self.contract_multiplier * super(FuturePosition, self).trading_pnl

    @property
    def position_pnl(self):
        # type: () -> float
        return self.contract_multiplier * super(FuturePosition, self).position_pnl

    @property
    def pnl(self):
        # type: () -> float
        return super(FuturePosition, self).pnl * self.contract_multiplier

    def calc_close_today_amount(self, trade_amount, position_effect):
        if position_effect == POSITION_EFFECT.CLOSE_TODAY:
            return trade_amount if trade_amount <= self.today_quantity else self.today_quantity
        else:
            return max(trade_amount - self._old_quantity, 0)

    def apply_trade(self, trade):
        if trade.position_effect == POSITION_EFFECT.CLOSE_TODAY:
            self._transaction_cost += trade.transaction_cost
            self._quantity -= trade.last_quantity
            self._trade_cost -= trade.last_price * trade.last_quantity
            self._queue.handle_trade(-trade.last_quantity, self._env.trading_dt.date(), close_today=True)
        else:
            super(FuturePosition, self).apply_trade(trade)

        if trade.position_effect == POSITION_EFFECT.OPEN:
            return -1 * trade.transaction_cost
        else:
            return -1 * trade.transaction_cost + (
                    trade.last_price - self._avg_price
            ) * trade.last_quantity * self.contract_multiplier * self._direction_factor

    @property
    def prev_close(self):
        if not is_valid_price(self._prev_close):
            if self._env.config.mod.sys_accounts.futures_settlement_price_type == "settlement":
                self._prev_close = self._env.data_proxy.get_prev_settlement(self._order_book_id, self._env.trading_dt)
            else:
                self._prev_close = super().prev_close
        return self._prev_close

    def settlement(self, trading_date):
        # type: (date) -> float
        delta_cash = super(FuturePosition, self).settlement(trading_date)
        if self._quantity == 0:
            return delta_cash
        data_proxy = self._env.data_proxy
        instrument = data_proxy.instrument(self._order_book_id)
        next_date = data_proxy.get_next_trading_date(trading_date)
        if self._env.config.mod.sys_accounts.futures_settlement_price_type == "settlement":
            # 逐日盯市按照结算价结算
            self._last_price = self._env.data_proxy.get_settle_price(self._order_book_id, self._env.trading_dt)
        delta_cash += self.equity
        self._avg_price = self.last_price
        if instrument.de_listed_at(next_date):
            user_system_log.warn(_(u"{order_book_id} is expired, close all positions by system").format(
                order_book_id=self._order_book_id
            ))
            account = self._env.get_account(self._order_book_id)
            side = SIDE.SELL if self.direction == POSITION_DIRECTION.LONG else SIDE.BUY
            trade = Trade.__from_create__(
                None, self.last_price, self._quantity, side, POSITION_EFFECT.CLOSE, self._order_book_id,
                transaction_cost=TransactionCost.zero()
            )
            self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=None))
            self._quantity = self._old_quantity = 0
            self._queue.clear()
        return delta_cash
    
    def post_settlement(self):
        try:
            del self.__dict__["margin_ratio"]
        except KeyError:
            pass


class StockPositionProxy(PositionProxy):
    __repr_properties__ = (
        "order_book_id", "quantity", "avg_price", "market_value"
    )
    __instrument_types__ = INST_TYPE_IN_STOCK_ACCOUNT

    @property
    def type(self):
        return "STOCK"

    @property
    def quantity(self):
        return self._long.quantity

    @property
    def sellable(self):
        """
        [int] 该仓位可卖出股数。T＋1 的市场中sellable = 所有持仓 - 今日买入的仓位 - 已冻结
        """
        return self._long.closable

    @property
    def avg_price(self):
        """
        [float] 平均开仓价格
        """
        return self._long.avg_price

    @property
    def value_percent(self):
        """
        [float] 获得该持仓的实时市场价值在股票投资组合价值中所占比例，取值范围[0, 1]
        """
        accounts = Environment.get_instance().portfolio.accounts
        if DEFAULT_ACCOUNT_TYPE.STOCK not in accounts:
            return 0
        total_value = accounts[DEFAULT_ACCOUNT_TYPE.STOCK].total_value
        return 0 if total_value == 0 else self.market_value / total_value


class FuturePositionProxy(PositionProxy):
    __repr_properties__ = (
        "order_book_id", "buy_quantity", "sell_quantity", "buy_market_value", "sell_market_value",
        "buy_margin", "sell_margin"
    )
    __instrument_types__ = [INSTRUMENT_TYPE.FUTURE]

    @property
    def type(self):
        return "FUTURE"

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
    def margin(self):
        """
        [float] 保证金

        保证金 = 持仓量 * 最新价 * 合约乘数 * 保证金率

        股票保证金 = 市值 = 持仓量 * 最新价

        """
        return self._long.margin + self._short.margin

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
        return self._long.today_closable

    @property
    def closable_today_buy_quantity(self):
        return self._long.today_closable

    @property
    def closable_buy_quantity(self):
        """
        [float] 可平多方向持仓
        """
        return self._long.closable

    @property
    def closable_sell_quantity(self):
        """
        [float] 可平空方向持仓
        """
        return self._short.closable

    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    buy_holding_pnl = deprecated_property("buy_holding_pnl", "buy_position_pnl")
    sell_holding_pnl = deprecated_property("sell_holding_pnl", "sell_position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
    buy_realized_pnl = deprecated_property("buy_realized_pnl", "buy_trading_pnl")
    sell_realized_pnl = deprecated_property("sell_realized_pnl", "sell_trading_pnl")
    buy_avg_holding_price = deprecated_property("buy_avg_holding_price", "buy_avg_open_price")
    sell_avg_holding_price = deprecated_property("sell_avg_holding_price", "sell_avg_open_price")
