from rqalpha.api import export_as_api
from rqalpha.execution_context import ExecutionContext
from rqalpha.const import EXECUTION_PHASE
from rqalpha.model.order import MarketOrder, LimitOrder
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.utils.functools import instype_singledispatch


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount').is_number(), verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_shares(id_or_ins, amount, price=None, style=None):
    raise NotImplementedError
