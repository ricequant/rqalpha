from typing import Tuple, Optional
from datetime import date

from rqalpha.model.trade import Trade
from rqalpha.const import POSITION_DIRECTION, SIDE, POSITION_EFFECT
from rqalpha.environment import Environment
from rqalpha.model.asset_position import AssetPosition


def _int_to_date(d):
    r, d = divmod(d, 100)
    y, m = divmod(r, 100)
    return date(year=y, month=m, day=d)


class StockPosition(AssetPosition):
    dividend_reinvestment = False  # type: Optional[Tuple[date, float, float]]

    def __init__(self, order_book_id, direction, t_plus_enabled=True):
        super(StockPosition, self).__init__(order_book_id, direction, t_plus_enabled)
        self._dividend_receivable = None

    def _handle_dividend_book_closure(self, trading_date, data_proxy):
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

        self._dividend_receivable = (payable_date, self.quantity, dividend_per_share)

        # if self.dividend_reinvestment:
        #     last_price = self.last_price
        #     dividend_value = self.quantity * dividend_per_share
        #     self.apply_trade(Trade.__from_create__(
        #         None, last_price, dividend_value / last_price, SIDE.BUY, POSITION_EFFECT.OPEN, self._order_book_id
        #     ))
        #     delta_static_total_value = dividend_value
        # else:
        #     self._dividend_receivable = (self.quantity, dividend_per_share)

    def _handle_dividend_payable(self, trading_date,  data_proxy):
        if not self._dividend_receivable:
            return
        payable_date, quantity, dividend_per_share = self._dividend_receivable
        if payable_date != trading_date:
            return
        if self.dividend_reinvestment:
            self.apply_trade()



    def _handle_transform(self):
        pass

    def _handle_split(self, trading_date, data_proxy):
        ratio = data_proxy.get_split_by_ex_date(self._order_book_id, trading_date)
        if ratio is None:
            return
        self.apply_split(ratio)

    def before_trading(self, trading_date):
        # type: (date) -> float
        if self.quantity == 0:
            return 0
        if self.direction != POSITION_DIRECTION.LONG:
            raise RuntimeError("direction of stock position {} is not supposed to be short".format(self._order_book_id))
        data_proxy = Environment.get_instance().data_proxy

        self._handle_dividend_book_closure(last_date, data_proxy)
        self._handle_dividend_payable(trading_date, data_proxy)
        self._handle_split(trading_date, data_proxy)
        self._handle_transform()

    @property
    def dividend_receivable(self):
        if self._dividend_receivable:
            _, quantity, dividend_per_share = self._dividend_receivable
            return quantity * dividend_per_share
        return 0

    @property
    def margin(self):
        return self.market_value + self.dividend_receivable
