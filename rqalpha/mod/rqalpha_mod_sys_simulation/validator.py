
from rqalpha.const import SIDE, INSTRUMENT_TYPE
from rqalpha.portfolio.account import Account
from rqalpha.model.trade import Trade
from rqalpha.environment import Environment
from rqalpha.model.order import ALGO_ORDER_STYLES, Order
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


def cash_enough(env, account, order, trade):
    # type: (Environment, Account, Order, Trade) -> bool

    trade_cost = trade.last_price * trade.last_quantity

    instrument = env.get_instrument(order.order_book_id)
    if instrument.type in [INSTRUMENT_TYPE.FUTURE, INSTRUMENT_TYPE.OPTION]:
        trade_cost *= instrument.margin_rate * env.config.base.margin_multiplier * instrument.contract_multiplier

    total_cash = account.cash + trade_cost
    if order.side == SIDE.SELL and total_cash < trade.transaction_cost:
        order.mark_rejected(
            "Order Cancelled: not enough money to sell {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}".format(
                order_book_id=order.order_book_id, cost_money=trade.transaction_cost, cash=total_cash
            ))
        return False

    total_cost = trade.transaction_cost + trade_cost
    if order.side == SIDE.BUY and total_cost > account.cash + order.init_frozen_cash:
        order.mark_rejected(
            "Order Cancelled: not enough money to buy {order_book_id}, needs {cost_money:.2f}, cash {cash:.2f}".format(
                order_book_id=order.order_book_id, cost_money=total_cost, cash=account.cash
            ))
        return False

    return True
