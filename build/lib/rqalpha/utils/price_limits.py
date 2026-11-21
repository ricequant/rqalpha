from typing import Union

from pandas import Series

from rqalpha.const import SIDE
from rqalpha.interface import AbstractPriceBoard
from rqalpha.utils import is_valid_price

PriceLike = Union[int, float]
PRICE_LIMIT_TOLERANCE = 1e-6


def reaches_limit_up(price: PriceLike, limit_up: PriceLike, tick_size: PriceLike) -> bool:
    if not (is_valid_price(price) and is_valid_price(limit_up)):
        return False
    return price >= limit_up - tick_size + PRICE_LIMIT_TOLERANCE


def reaches_limit_down(price: PriceLike, limit_down: PriceLike, tick_size: PriceLike) -> bool:
    if not (is_valid_price(price) and is_valid_price(limit_down)):
        return False
    return price <= limit_down + tick_size - PRICE_LIMIT_TOLERANCE


def reaches_limit(
    order_book_id: str,
    price: PriceLike,
    side: SIDE,
    price_board: AbstractPriceBoard,
    tick_size: PriceLike,
) -> bool:
    if side == SIDE.BUY:
        return reaches_limit_up(price, price_board.get_limit_up(order_book_id), tick_size)
    if side == SIDE.SELL:
        return reaches_limit_down(price, price_board.get_limit_down(order_book_id), tick_size)
    raise ValueError("unsupport side: {}".format(side))


def _is_valid_price_series(values: Series) -> Series:
    return values.notna() & values.gt(0)


def reaches_limit_up_vectorized(prices: Series, limit_up: Series, tick_sizes: Series) -> Series:
    valid_price = _is_valid_price_series(prices)
    valid_limit = _is_valid_price_series(limit_up)

    thresholds = limit_up - tick_sizes + PRICE_LIMIT_TOLERANCE
    return valid_price & valid_limit & prices.ge(thresholds)


def reaches_limit_down_vectorized(prices: Series, limit_down: Series, tick_sizes: Series) -> Series:
    valid_price = _is_valid_price_series(prices)
    valid_limit = _is_valid_price_series(limit_down)

    thresholds = limit_down + tick_sizes - PRICE_LIMIT_TOLERANCE
    return valid_price & valid_limit & prices.le(thresholds)
