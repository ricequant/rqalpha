from typing import Union, List

from rqalpha.model.order import OrderStyle, Order
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION

from .api_stock import order_shares


def order_stock(order_book_id, quantity, style, target):
    # type: (str, Union[int, float], OrderStyle, bool) -> List[Order]
    position = Environment.get_instance().portfolio.get_position(order_book_id, POSITION_DIRECTION.LONG)
    if target:
        quantity = quantity - position.quantity
    return order_shares(order_book_id, quantity, style=style)
