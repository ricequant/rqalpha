from typing import Optional

from rqalpha.interface import AbstractFrontendValidator
from rqalpha.utils.logger import user_system_log
from rqalpha.model.order import Order
from rqalpha.portfolio.account import Account


class MarginComponentValidator(AbstractFrontendValidator):
    """ 融资融券股票池验证 """

    def __init__(self, margin_type="all"):
        self._margin_type = margin_type
        from rqalpha.apis.api_rqdatac import get_margin_stocks
        self._get_margin_stocks = get_margin_stocks
        
    def validate_submission(self, order: Order, account: Optional[Account] = None) -> Optional[str]:
        # 没负债等于没融资，则不需要限制股票池
        if account.cash_liabilities == 0:
            return None
        symbols = self._get_margin_stocks(margin_type=self._margin_type)
        # 是否在股票池中
        if order.order_book_id in set(symbols):
            return None
        else:
            reason = "Order Creation Failed: margin stock pool not contains {}.".format(order.order_book_id)
            return reason
    
    def validate_cancellation(self, order: Order, account: Optional[Account] = None) -> Optional[str]:
        return None
