from typing import Optional

from rqalpha.interface import AbstractFrontendValidator
from rqalpha.utils.logger import user_system_log
from rqalpha.model.order import Order
from rqalpha.portfolio.account import Account
from rqalpha.environment import Environment


class MarginComponentValidator(AbstractFrontendValidator):
    """ 融资融券股票池验证 """

    def __init__(self, margin_type="all"):
        self._margin_type = margin_type
        from rqalpha.apis.api_rqdatac import get_margin_stocks
        self._get_margin_stocks = get_margin_stocks

    def can_cancel_order(self, order, account=None):
        return True

    def can_submit_order(self, order, account=None):
        # type: (Order, Optional[Account]) -> bool

        trade_dt = Environment.get_instance().trading_dt

        symbols = self._get_margin_stocks(exchange=None, margin_type=self._margin_type)

        if order.order_book_id in set(symbols):
            return True
        else:
            user_system_log.warn("Order Creation Failed: date {}, margin stock pool not contains {}.".format(
                trade_dt.date(), order.order_book_id)
            )
            return False
