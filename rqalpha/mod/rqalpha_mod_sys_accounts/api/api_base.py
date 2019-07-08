from functools import reduce
from operator import add

from six import itervalues

from rqalpha.api.api_base import decorate_api_exc
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.const import POSITION_DIRECTION
from rqalpha.environment import Environment


__all__ = [

]


def export_as_api(func):
    __all__.append(func.__name__)
    return decorate_api_exc(func)


@export_as_api
def get_positions():
    portfolio = Environment.get_instance().portfolio
    return reduce(add, (reduce(add, (
        p.positions for p in itervalues(a.positions)
    ), []) for a in itervalues(portfolio.accounts)), [])


@export_as_api
@apply_rules(
    verify_that("direction").is_in([POSITION_DIRECTION.LONG, POSITION_DIRECTION.SHORT])
)
def get_position(order_book_id, direction):
    position_proxy = Environment.get_instance().portfolio.positions[order_book_id]
    if direction == POSITION_DIRECTION.LONG:
        return position_proxy.long
    else:
        return position_proxy.short
