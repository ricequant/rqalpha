from unittest.mock import Mock, patch

import pytest
from pandas import Series

from rqalpha.const import INSTRUMENT_TYPE, MARKET, POSITION_EFFECT, SIDE
from rqalpha.mod.rqalpha_mod_sys_accounts.api.order_target_portfolio import OrderTargetPortfolio
from rqalpha.interface import AbstractTransactionCostDecider, TransactionCost, TransactionCostArgs
from rqalpha.model.instrument import Instrument
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders import (
    AbstractStockTransactionCostDecider,
    CommissionProfile,
    ETFTransactionCostDecider,
    StockTransactionCostDecider,
)
from rqalpha.mod.rqalpha_mod_sys_transaction_cost.mod import TransactionCostMod
from rqalpha.utils import RqAttrDict


KNOWN_DEFAULT_FUND_TYPES = [
    "Stock",
    "Hybrid",
    "StockIndex",
    "Related",
    "QDII",
    "Other",
]


def make_etf(fund_type="Stock", order_book_id="510300.XSHG"):
    data = {
        "order_book_id": order_book_id,
        "symbol": order_book_id,
        "type": "ETF",
        "exchange": "XSHG",
        "fund_type": fund_type,
    }
    if fund_type is None:
        data.pop("fund_type")
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


def make_decider():
    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance"
    ):
        return ETFTransactionCostDecider(
            default_profile=CommissionProfile(commission_rate=0.0008, min_commission=5),
            subtype_profiles={
                "bond": CommissionProfile(commission_rate=0.0002, min_commission=1),
                "money": CommissionProfile(commission_rate=0, min_commission=0),
            },
        )


@pytest.mark.parametrize("fund_type", ["Bond", "BondIndex", "ShortBond"])
def test_bond_fund_types_use_bond_profile(fund_type):
    cost = make_decider().calc(make_args(make_etf(fund_type), quantity=1000, price=10))

    assert cost.commission == 2
    assert cost.tax == 0


def test_money_fund_type_accepts_explicit_zero_profile():
    cost = make_decider().calc(make_args(make_etf("Money")))

    assert cost.commission == 0
    assert cost.tax == 0


@pytest.mark.parametrize("fund_type", KNOWN_DEFAULT_FUND_TYPES)
def test_other_known_fund_types_use_default_profile(fund_type):
    cost = make_decider().calc(make_args(make_etf(fund_type)))

    assert cost.commission == 8


def test_missing_fund_type_fails():
    with pytest.raises(KeyError, match="fund_type"):
        make_decider().calc(make_args(make_etf(None)))


def test_unknown_fund_type_uses_default_profile():
    cost = make_decider().calc(make_args(make_etf("Unknown")))

    assert cost.commission == 8


def test_partial_fills_charge_minimum_commission_once_per_order():
    decider = make_decider()
    instrument = make_etf("Bond")

    first = decider.calc(make_args(instrument, quantity=100, price=10, order_id=1))
    second = decider.calc(make_args(instrument, quantity=2500, price=10, order_id=1))
    another_order = decider.calc(make_args(instrument, quantity=100, price=10, order_id=2))

    assert first.commission == 1
    assert second.commission == 4.2
    assert another_order.commission == 1


def test_zero_rate_charges_nonzero_minimum_once_per_order():
    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance"
    ):
        decider = ETFTransactionCostDecider(
            default_profile=CommissionProfile(commission_rate=0, min_commission=5),
            subtype_profiles={
                "bond": CommissionProfile(commission_rate=0, min_commission=5),
                "money": CommissionProfile(commission_rate=0, min_commission=5),
            },
        )
    instrument = make_etf("Stock")

    costs = [
        decider.calc(make_args(instrument, quantity=100, price=10, order_id=1)).commission
        for _ in range(3)
    ]

    assert costs == [5, 0, 0]


def test_shared_commission_calculation_preserves_legacy_stock_zero_multiplier_behavior():
    with patch(
        "rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance"
    ):
        decider = StockTransactionCostDecider(
            commission_multiplier=0,
            min_commission=5,
            tax_multiplier=1,
            pit_tax=False,
            event_bus=Mock(),
        )
    stock = Instrument({
        "order_book_id": "000001.XSHE",
        "symbol": "平安银行",
        "type": "CS",
        "exchange": "XSHE",
    })

    costs = [
        decider.calc(make_args(stock, quantity=100, price=10, order_id=1)).commission
        for _ in range(3)
    ]

    assert costs == [5, 5, 5]


def test_etf_sell_never_charges_stock_stamp_tax():
    cost = make_decider().calc(make_args(make_etf(), side=SIDE.SELL))

    assert cost.commission == 8
    assert cost.tax == 0


def test_batch_estimate_uses_each_etf_profile():
    instruments = Series({
        "510300.XSHG": make_etf("Stock", "510300.XSHG"),
        "511010.XSHG": make_etf("BondIndex", "511010.XSHG"),
        "511880.XSHG": make_etf("Money", "511880.XSHG"),
    })
    quantities = Series({"510300.XSHG": -1000, "511010.XSHG": 1000, "511880.XSHG": -1000})
    prices = Series({"510300.XSHG": 10, "511010.XSHG": 10, "511880.XSHG": 10})

    decider = make_decider()
    decider.env = Mock()
    decider.env.data_proxy.get_active_instruments.return_value = instruments.to_dict()

    costs = decider.batch_estimate(quantities, prices)

    assert costs.to_dict() == {
        "510300.XSHG": 8,
        "511010.XSHG": 2,
        "511880.XSHG": 0,
    }


def test_smart_portfolio_estimate_falls_back_for_calc_only_custom_etf_decider():
    env = Mock()
    with patch("rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance", return_value=env):
        stock_decider = StockTransactionCostDecider(
            commission_multiplier=1,
            min_commission=0,
            tax_multiplier=2,
            pit_tax=False,
            event_bus=Mock(),
        )
    class LegacyStockDecider(AbstractStockTransactionCostDecider):
        def calc(self, args):
            return stock_decider.calc(args)

        def batch_estimate(self, delta_quantities, prices):
            return stock_decider.batch_estimate(delta_quantities, prices)

    class CalcOnlyETFDecider(AbstractTransactionCostDecider):
        def calc(self, args):
            return TransactionCost.zero()

    deciders = {
        (INSTRUMENT_TYPE.CS, MARKET.CN): LegacyStockDecider(),
        (INSTRUMENT_TYPE.ETF, MARKET.CN): CalcOnlyETFDecider(),
    }
    env.get_transaction_cost_decider.side_effect = lambda instrument_type, market: deciders[
        instrument_type, market
    ]

    portfolio = object.__new__(OrderTargetPortfolio)
    portfolio._env = env
    portfolio._market = Series({
        "000001.XSHE": MARKET.CN,
        "113000.XSHG": MARKET.CN,
        "511880.XSHG": MARKET.CN,
    })
    portfolio._instrument_types = Series({
        "000001.XSHE": INSTRUMENT_TYPE.CS,
        "113000.XSHG": INSTRUMENT_TYPE.CONVERTIBLE,
        "511880.XSHG": INSTRUMENT_TYPE.ETF,
    })
    portfolio._exchange_rates = {}

    costs = portfolio._estimate_transaction_costs(
        Series({"000001.XSHE": -1000, "113000.XSHG": -1000, "511880.XSHG": -1000}),
        Series({"000001.XSHE": 10, "113000.XSHG": 10, "511880.XSHG": 10}),
    )

    assert costs == 39


def test_smart_portfolio_estimate_uses_etf_subtype_profile():
    env = Mock()
    decider = make_decider()
    decider.env = env
    env.data_proxy.get_active_instruments.return_value = {
        "511010.XSHG": make_etf("BondIndex", "511010.XSHG")
    }
    env.get_transaction_cost_decider.return_value = decider
    portfolio = object.__new__(OrderTargetPortfolio)
    portfolio._env = env
    portfolio._market = Series({"511010.XSHG": MARKET.CN})
    portfolio._instrument_types = Series({"511010.XSHG": INSTRUMENT_TYPE.ETF})
    portfolio._exchange_rates = {}

    costs = portfolio._estimate_transaction_costs(
        Series({"511010.XSHG": 1000}),
        Series({"511010.XSHG": 10}),
    )

    assert costs == 2


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


def start_mod(etf_commission):
    env = Mock()
    env.event_bus = Mock()
    deciders = {}
    env.set_transaction_cost_decider.side_effect = lambda instrument_type, decider: deciders.__setitem__(
        instrument_type, decider
    )
    with patch("rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance", return_value=env):
        TransactionCostMod().start_up(env, make_mod_config(etf_commission))
    return deciders


def test_all_none_etf_config_inherits_effective_stock_profile():
    deciders = start_mod({
        "default": {"commission_rate": None, "min_commission": None},
        "subtypes": {
            "bond": {"commission_rate": None, "min_commission": None},
            "money": {"commission_rate": None, "min_commission": None},
        },
    })

    etf_decider = deciders[INSTRUMENT_TYPE.ETF]
    default_cost = etf_decider.calc(make_args(make_etf("Stock"), quantity=1000, price=10))
    assert default_cost.commission == 16
    with pytest.raises(KeyError, match="fund_type"):
        etf_decider.calc(make_args(make_etf(None), quantity=1000, price=10))


def test_startup_without_etf_config_inherits_stock_profile():
    config = make_mod_config({})
    del config.etf_commission
    env = Mock()
    env.event_bus = Mock()
    deciders = {}
    env.set_transaction_cost_decider.side_effect = lambda instrument_type, decider: deciders.__setitem__(
        instrument_type, decider
    )

    with patch("rqalpha.mod.rqalpha_mod_sys_transaction_cost.deciders.Environment.get_instance", return_value=env):
        TransactionCostMod().start_up(env, config)

    cost = deciders[INSTRUMENT_TYPE.ETF].calc(make_args(make_etf("Stock"), quantity=1000, price=10))
    assert cost.commission == 16


def test_etf_config_inherits_each_field_independently():
    deciders = start_mod({
        "default": {"commission_rate": 0.0005, "min_commission": None},
        "subtypes": {
            "bond": {"commission_rate": None, "min_commission": 0},
            "money": {"commission_rate": 0, "min_commission": None},
        },
    })
    etf_decider = deciders[INSTRUMENT_TYPE.ETF]

    default_cost = etf_decider.calc(make_args(make_etf("Stock"), quantity=100, price=10))
    bond_cost = etf_decider.calc(make_args(make_etf("Bond"), quantity=100, price=10))
    money_cost = etf_decider.calc(make_args(make_etf("Money"), quantity=100, price=10))

    assert default_cost.commission == 3
    assert bond_cost.commission == 0.5
    assert money_cost.commission == 3


@pytest.mark.parametrize(
    "etf_commission, error",
    [
        ({"default": {"commission_rate": -0.1, "min_commission": None}, "subtypes": {}}, "commission_rate"),
        ({"default": {"commission_rate": float("nan"), "min_commission": None}, "subtypes": {}}, "commission_rate"),
        ({"default": {"commission_rate": None, "min_commission": None, "typo": 1}, "subtypes": {}}, "typo"),
        ({"default": {"commission_rate": None, "min_commission": None}, "subtypes": {"gold": {}}}, "gold"),
    ],
)
def test_invalid_etf_config_is_rejected(etf_commission, error):
    with pytest.raises(ValueError, match=error):
        start_mod(etf_commission)
