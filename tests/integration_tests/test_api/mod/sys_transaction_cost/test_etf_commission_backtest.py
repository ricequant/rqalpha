import pytest

from rqalpha import run_func
from rqalpha.apis import order_shares, order_target_portfolio


def make_config():
    return {
        "base": {
            "start_date": "2022-01-04",
            "end_date": "2022-01-04",
            "frequency": "1d",
            "accounts": {"stock": 1_000_000},
            "capital_gain_tax_rate": 0,
        },
        "mod": {
            "sys_analyser": {"enabled": False},
            "sys_transaction_cost": {
                "etf_commission": {
                    "default": {"commission_rate": None, "min_commission": None},
                    "subtypes": {
                        "bond": {"commission_rate": 0.0002, "min_commission": 0},
                        "money": {"commission_rate": 0, "min_commission": 0},
                    },
                },
            },
        },
    }


def assert_etf_transaction_costs(bond_order, money_order):
    assert bond_order.transaction_cost == pytest.approx(
        bond_order.avg_price * bond_order.filled_quantity * 0.0002
    )
    assert money_order.transaction_cost == 0


def test_etf_commission_profiles_apply_to_backtest_trades():

    def init(context):
        context.ordered = False

    def handle_bar(context, _bar_dict):
        if context.ordered:
            return
        context.ordered = True
        bond_order = order_shares("511010.XSHG", 1000)
        money_order = order_shares("511880.XSHG", 1000)

        assert_etf_transaction_costs(bond_order, money_order)

    run_func(config=make_config(), init=init, handle_bar=handle_bar)


def test_etf_commission_profiles_apply_to_order_target_portfolio():
    def handle_bar(context, _bar_dict):
        if getattr(context, "ordered", False):
            return
        context.ordered = True
        orders = order_target_portfolio({
            "511010.XSHG": 0.1,
            "511880.XSHG": 0.1,
        })
        orders_by_id = {order.order_book_id: order for order in orders}

        assert_etf_transaction_costs(
            orders_by_id["511010.XSHG"], orders_by_id["511880.XSHG"]
        )

    run_func(config=make_config(), handle_bar=handle_bar)
