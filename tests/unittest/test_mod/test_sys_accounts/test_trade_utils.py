from datetime import datetime
from types import SimpleNamespace

from rqalpha.const import MARKET
from rqalpha.interface import ExchangeRate, TransactionCost
from rqalpha.mod.rqalpha_mod_sys_accounts.trade_utils import get_amount_from_value


def test_get_amount_from_value_uses_ask_exchange_rate_for_buying_power():
    env = SimpleNamespace(
        trading_dt=datetime(2026, 1, 5),
        data_proxy=SimpleNamespace(
            get_exchange_rate=lambda _date, _market: ExchangeRate(
                bid_reference=1,
                ask_reference=2,
                bid_settlement_sh=1,
                ask_settlement_sh=2,
                bid_settlement_sz=1,
                ask_settlement_sz=2,
            )
        ),
        calc_transaction_cost=lambda _args: TransactionCost.zero(),
    )
    ins = SimpleNamespace(
        type="CS",
        board_type="MAIN",
        round_lot=100,
        order_step_size=100,
        market=MARKET.HK,
    )

    assert get_amount_from_value(100000, ins, 100, env, account_cash=200000) == 500
