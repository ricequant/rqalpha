
from rqalpha.model.order import ALGO_ORDER_STYLES
from rqalpha.interface import AbstractFrontendValidator


class OrderStyleValidator(AbstractFrontendValidator):

    def __init__(self, frequency):
        self._frequency = frequency

    def can_submit_order(self, order, account=None):
        if isinstance(order.style, ALGO_ORDER_STYLES) and self._frequency in ["1m", "tick"]:
            raise RuntimeError("algo order no support 1m or tick frequency")
        return True

    def can_cancel_order(self, order, account=None):
        return True

