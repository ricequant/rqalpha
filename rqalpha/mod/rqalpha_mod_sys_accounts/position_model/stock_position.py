from typing import Tuple, Optional
from datetime import date

from rqalpha.model.trade import Trade
from rqalpha.const import POSITION_DIRECTION, SIDE, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.model.asset_position import AssetPosition, DeltaPosition
from rqalpha.data.data_proxy import DataProxy

from ..api.api_stock import order_shares


def _int_to_date(d):
    r, d = divmod(d, 100)
    y, m = divmod(r, 100)
    return date(year=y, month=m, day=d)


class StockPosition(AssetPosition):
    dividend_reinvestment = False
    cash_return_by_stock_delisted = True
    t_plus_enabled = True
    enable_position_validator = True

    def __init__(self, order_book_id, direction):
        super(StockPosition, self).__init__(order_book_id, direction)
        self._dividend_receivable = None
        self._pending_transform = None

    @property
    def dividend_receivable(self):
        if self._dividend_receivable:
            _, dividend_value = self._dividend_receivable
            return dividend_value
        return 0

    @property
    def receivable(self):
        return self.dividend_receivable

    @property
    def closable(self):
        order_quantity = sum(o for o in self._open_orders if o.position_effect in (
            POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY, POSITION_EFFECT.EXERCISE
        ))
        if self.t_plus_enabled:
            return self.quantity - order_quantity - self._non_closable
        return self.quantity - order_quantity

    @property
    def position_validator_enabled(self):
        return self.enable_position_validator

    def set_state(self, state):
        super(StockPosition, self).set_state(state)
        self._dividend_receivable = state.get("dividend_receivable")
        self._pending_transform = state.get("pending_transform")

    def get_state(self):
        state = super(StockPosition, self).get_state()
        state.update({
            "dividend_receivable": self._dividend_receivable,
            "pending_transform": self._pending_transform,
        })

    def before_trading(self, trading_date):
        # type: (date) -> float
        delta_static_total_value = super(StockPosition, self).before_trading(trading_date)
        if self.quantity == 0:
            return delta_static_total_value
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        data_proxy = Environment.get_instance().data_proxy
        self._handle_dividend_book_closure(trading_date, data_proxy)
        delta_static_total_value += self._handle_dividend_payable(trading_date)
        self._handle_split(trading_date, data_proxy)

    def settlement(self, trading_date):
        # type: (date) -> Tuple[float, Optional[Trade]]
        delta_static_total_value, _ = super(StockPosition, self).settlement(trading_date)
        virtual_trade = None
        if self.quantity == 0:
            return 0, None
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        data_proxy = Environment.get_instance().data_proxy
        next_date = data_proxy.get_next_trading_date(trading_date)
        instrument = data_proxy.instruments(self._order_book_id)
        if instrument.de_listed_at(next_date):
            try:
                transform_data = data_proxy.get_share_transformation(self._order_book_id)
            except NotImplementedError:
                pass
            else:
                if transform_data is not None:
                    successor, conversion_ratio = transform_data
                    virtual_trade = Trade.__from_create__(
                        order_id=None,
                        price=self.avg_price / conversion_ratio,
                        amount=self.quantity * conversion_ratio,
                        side=SIDE.BUY,
                        position_effect=POSITION_EFFECT.OPEN,
                        order_book_id=successor
                    )
            if virtual_trade is None and not self.cash_return_by_stock_delisted:
                delta_static_total_value -= self.market_value
        return delta_static_total_value, virtual_trade

    def order(self, quantity, style, target=False):
        if target:
            quantity = quantity - self,quantity
        return order_shares(self._order_book_id, quantity, style=style)

    def calc_close_today_amount(self, trade_amount):
        return 0

    def _handle_dividend_book_closure(self, trading_date, data_proxy):
        # type: (date, DataProxy) -> None
        last_date = data_proxy.get_previous_trading_date(trading_date)
        dividend = data_proxy.get_dividend_by_book_date(self._order_book_id, last_date)
        if dividend is None:
            return
        dividend_per_share = sum(dividend['dividend_cash_before_tax'] / dividend['round_lot'])
        if dividend_per_share != dividend_per_share:
            raise RuntimeError("Dividend per share of {} is not supposed to be nan.".format(self._order_book_id))
        self.apply_dividend(dividend_per_share)

        try:
            payable_date = _int_to_date(dividend["payable_date"][0])
        except ValueError:
            payable_date = _int_to_date(dividend["ex_dividend_date"][0])

        self._dividend_receivable = (payable_date, self.quantity * dividend_per_share)

    def _handle_dividend_payable(self, trading_date):
        # type: (date) -> float
        # 返回静态权益的变化量
        if not self._dividend_receivable:
            return 0
        payable_date, dividend_value = self._dividend_receivable
        if payable_date != trading_date:
            return 0
        if self.dividend_reinvestment:
            last_price = self.last_price
            self.apply_trade(Trade.__from_create__(
                None, last_price, dividend_value / last_price, SIDE.BUY, POSITION_EFFECT.OPEN, self._order_book_id
            ))
        self._dividend_receivable = None
        return dividend_value

    def _handle_split(self, trading_date, data_proxy):
        ratio = data_proxy.get_split_by_ex_date(self._order_book_id, trading_date)
        if ratio is None:
            return
        self.apply_split(ratio)
