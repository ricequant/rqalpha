from typing import Union, Callable
from decimal import Decimal

from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument
from rqalpha.const import SIDE, POSITION_EFFECT
from rqalpha.interface import TransactionCostArgs


KSH_MIN_AMOUNT = 200
BJSE_MIN_AMOUNT = 100


def estimate_transaction_cost_calculator(env: Environment, ins: Instrument, delta_quantity: Union[int, float], price: float) -> float:
    if delta_quantity > 0:
        side, position_effect = SIDE.BUY, POSITION_EFFECT.OPEN
    else:
        side, position_effect = SIDE.SELL, POSITION_EFFECT.CLOSE
    return env.calc_transaction_cost(TransactionCostArgs(
        ins, price, abs(delta_quantity), side, position_effect,  # type: ignore
    )).total


def round_order_quantity(ins, quantity, method: Callable = int) -> int:
    if ins.type == "CS" and ins.board_type == "KSH":
        # KSH can buy(sell) 201, 202 shares
        return 0 if abs(quantity) < KSH_MIN_AMOUNT else int(quantity)
    elif ins.type == "CS" and ins.board_type == "BJS":
        # BJSE can buy(sell) 101, 202 shares
        return 0 if abs(quantity) < BJSE_MIN_AMOUNT else int(quantity)
    else:
        round_lot = ins.round_lot
        try:
            return method(Decimal(quantity) / Decimal(round_lot)) * round_lot
        except ValueError:
            raise