from typing import Union, Callable
from decimal import Decimal

from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument
from rqalpha.const import SIDE, POSITION_EFFECT
from rqalpha.interface import TransactionCostArgs
from rqalpha.mod.utils import round_order_quantity


def estimate_transaction_cost_calculator(env: Environment, ins: Instrument, delta_quantity: Union[int, float], price: float) -> float:
    if delta_quantity > 0:
        side, position_effect = SIDE.BUY, POSITION_EFFECT.OPEN
    else:
        side, position_effect = SIDE.SELL, POSITION_EFFECT.CLOSE
    return env.calc_transaction_cost(TransactionCostArgs(
        ins, price, abs(delta_quantity), side, position_effect,  # type: ignore
    )).total


def get_amount_from_value(value: float, ins: Instrument, price: float, env: Environment, account_cash: float) -> int:
    exchange_rates = env.data_proxy.get_exchange_rate(env.trading_dt.date(), ins.market)
    exchange_rate_middle = (exchange_rates.bid_reference + exchange_rates.ask_reference) / 2
    amount = int(Decimal(value) / Decimal(price * exchange_rate_middle))
    if value > 0:
        amount = min(amount, int(Decimal(account_cash) / Decimal(price * exchange_rates.ask_reference)))
        amount = round_order_quantity(ins, amount)
        while amount > 0:
            estimate_transaction_cost = estimate_transaction_cost_calculator(env, ins, amount, price)
            if amount * price * exchange_rates.ask_reference + estimate_transaction_cost > value:
                amount = round_order_quantity(ins, amount - ins.order_step_size)
            else:
                return amount
    return amount
