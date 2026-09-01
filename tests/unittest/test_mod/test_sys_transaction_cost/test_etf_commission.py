from unittest.mock import Mock, call, patch

import pytest
from pandas import Series

from rqalpha.const import INSTRUMENT_TYPE, MARKET, POSITION_EFFECT, SIDE
from rqalpha.interface import TransactionCost, TransactionCostArgs
from rqalpha.model.instrument import Instrument
from rqalpha.mod.rqalpha_mod_sys_accounts.api.order_target_portfolio import OrderTargetPortfolio
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders import (
    AbstractStockTransactionCostDecider,
    CommissionProfile,
    ETFTransactionCostDecider,
    StockTransactionCostDecider,
)
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.mod import TransactionCostMod
from rqalpha.utils import RqAttrDict


def make_instrument(
    instrument_type=INSTRUMENT_TYPE.ETF,
    fund_type="Stock",
    order_book_id="510300.XSHG",
):
    data = {
        "order_book_id": order_book_id,
        "symbol": order_book_id,
        "type": instrument_type.name,
        "exchange": "XSHG",
    }
    if fund_type is not None:
        data["fund_type"] = fund_type
    return Instrument(data)


def make_args(instrument, *, quantity=1000, price=10, side=SIDE.BUY, order_id=None):
    return TransactionCostArgs(
        instrument=instrument,
        price=price,
        quantity=quantity,
        side=side,
        position_effect=POSITION_EFFECT.OPEN if side == SIDE.BUY else POSITION_EFFECT.CLOSE,
        order_id=order_id,
    )


def make_decider(default_profile=None):
    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance"
    ):
        return ETFTransactionCostDecider(
            default_profile=default_profile or CommissionProfile(0.0008, 5),
            subtype_profiles={
                "bond": CommissionProfile(0.0002, 1),
                "money": CommissionProfile(0, 0),
            },
        )


def test_etf_profile_selection_tax_and_missing_metadata():
    decider = make_decider()
    expected_commissions = {
        "Bond": 2,
        "BondIndex": 2,
        "ShortBond": 2,
        "Money": 0,
        "Stock": 8,
        "UnknownFutureType": 8,
    }

    for fund_type, expected in expected_commissions.items():
        cost = decider.calc(make_args(make_instrument(fund_type=fund_type)))
        assert cost.commission == expected
        assert cost.tax == 0

    assert decider.calc(make_args(make_instrument(), side=SIDE.SELL)).tax == 0
    with pytest.raises(KeyError, match="fund_type"):
        decider.calc(make_args(make_instrument(fund_type=None)))


def test_commission_state_handles_etf_profiles_and_preserves_stock_behavior():
    bond_decider = make_decider()
    bond = make_instrument(fund_type="Bond")
    assert [
        bond_decider.calc(make_args(bond, quantity=quantity, order_id=1)).commission
        for quantity in (100, 2500)
    ] == [1, 4.2]
    assert bond_decider.calc(make_args(bond, quantity=100, order_id=2)).commission == 1

    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance"
    ):
        stock_decider = StockTransactionCostDecider(0, 5, 1, False, Mock())
    stock = make_instrument(INSTRUMENT_TYPE.CS, fund_type=None, order_book_id="000001.XSHE")
    assert [
        stock_decider.calc(make_args(stock, quantity=100, order_id=1)).commission
        for _ in range(3)
    ] == [5, 5, 5]


def test_batch_estimate_uses_each_etf_profile():
    instruments = {
        "510300.XSHG": make_instrument(order_book_id="510300.XSHG"),
        "511010.XSHG": make_instrument(INSTRUMENT_TYPE.ETF, "BondIndex", "511010.XSHG"),
        "511880.XSHG": make_instrument(INSTRUMENT_TYPE.ETF, "Money", "511880.XSHG"),
    }
    quantities = Series({order_book_id: -1000 for order_book_id in instruments})
    prices = Series({order_book_id: 10 for order_book_id in instruments})
    decider = make_decider()
    decider.env = Mock()
    decider.env.data_proxy.get_active_instruments.return_value = instruments

    costs = decider.batch_estimate(quantities, prices)

    assert costs.to_dict() == {
        "510300.XSHG": 8,
        "511010.XSHG": 2,
        "511880.XSHG": 0,
    }


class FixedBatchDecider(AbstractStockTransactionCostDecider):
    def __init__(self, cost):
        self.cost = cost

    def calc(self, args):
        return TransactionCost.zero()

    def batch_estimate(self, delta_quantities, prices):
        return Series(self.cost, index=delta_quantities.index, dtype=float)


def test_smart_portfolio_uses_etf_decider_only_for_etfs():
    env = Mock()
    deciders = {
        (INSTRUMENT_TYPE.CS, MARKET.CN): FixedBatchDecider(1),
        (INSTRUMENT_TYPE.ETF, MARKET.CN): FixedBatchDecider(2),
    }
    env.get_transaction_cost_decider.side_effect = lambda instrument_type, market: deciders[
        instrument_type, market
    ]
    portfolio = object.__new__(OrderTargetPortfolio)
    portfolio._env = env
    portfolio._market = Series({
        order_book_id: MARKET.CN
        for order_book_id in ("stock", "etf", "lof", "convertible")
    })
    portfolio._instrument_types = Series({
        "stock": INSTRUMENT_TYPE.CS,
        "etf": INSTRUMENT_TYPE.ETF,
        "lof": INSTRUMENT_TYPE.LOF,
        "convertible": INSTRUMENT_TYPE.CONVERTIBLE,
    })
    portfolio._exchange_rates = {}

    costs = portfolio._estimate_transaction_costs(
        Series({"stock": -1000, "etf": -1000, "lof": -1000, "convertible": -1000}),
        Series({"stock": 10, "etf": 10, "lof": 10, "convertible": 10}),
    )

    assert costs == 5
    assert env.get_transaction_cost_decider.call_args_list == [
        call(INSTRUMENT_TYPE.CS, MARKET.CN),
        call(INSTRUMENT_TYPE.ETF, MARKET.CN),
    ]


def make_mod_config(etf_commission):
    return RqAttrDict({
        "stock_commission_multiplier": 2,
        "stock_min_commission": 3,
        "cn_stock_min_commission": None,
        "futures_commission_multiplier": 1,
        "tax_multiplier": 1,
        "pit_tax": False,
        "etf_commission": etf_commission,
    })


def start_mod(etf_commission, *, omit_etf_config=False):
    config = make_mod_config(etf_commission)
    if omit_etf_config:
        del config.etf_commission
    env = Mock()
    env.event_bus = Mock()
    deciders = {}
    env.set_transaction_cost_decider.side_effect = lambda instrument_type, decider: deciders.__setitem__(
        instrument_type, decider
    )
    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance",
        return_value=env,
    ):
        TransactionCostMod().start_up(env, config)
    return deciders


def test_etf_config_resolves_inheritance_per_field():
    inherited = start_mod({}, omit_etf_config=True)[INSTRUMENT_TYPE.ETF]
    assert inherited.calc(make_args(make_instrument())).commission == 16

    configured = start_mod({
        "default": {"commission_rate": 0.0005, "min_commission": None},
        "subtypes": {
            "bond": {"commission_rate": None, "min_commission": 0},
            "money": {"commission_rate": 0, "min_commission": 0},
        },
    })[INSTRUMENT_TYPE.ETF]
    assert {
        fund_type: configured.calc(
            make_args(make_instrument(fund_type=fund_type), quantity=100)
        ).commission
        for fund_type in ("Stock", "Bond", "Money")
    } == {"Stock": 3, "Bond": 0.5, "Money": 0}

    with pytest.raises(KeyError, match="fund_type"):
        configured.calc(make_args(make_instrument(fund_type=None)))


def test_invalid_etf_configs_are_rejected():
    cases = [
        ({"default": {"commission_rate": -0.1}, "subtypes": {}}, "commission_rate"),
        ({"default": {"commission_rate": float("nan")}, "subtypes": {}}, "commission_rate"),
        ({"default": {"commission_rate": 0, "min_commission": 1}, "subtypes": {}}, "min_commission"),
        ({
            "default": {"commission_rate": 0.0005, "min_commission": 1},
            "subtypes": {"money": {"commission_rate": 0}},
        }, "min_commission"),
        ({"default": {"typo": 1}, "subtypes": {}}, "typo"),
        ({"default": {}, "subtypes": {"gold": {}}}, "gold"),
    ]
    for config, error in cases:
        with pytest.raises(ValueError, match=error):
            start_mod(config)
