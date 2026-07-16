from types import SimpleNamespace

import pytest

from rqalpha.const import RUN_TYPE
from rqalpha.mod.rqalpha_mod_sys_risk import mod as risk_mod
from rqalpha.mod.rqalpha_mod_sys_risk.mod import RiskManagerMod


def make_env(partial_fill_on_insufficient_cash):
    return SimpleNamespace(
        config=SimpleNamespace(
            base=SimpleNamespace(
                partial_fill_on_insufficient_cash=partial_fill_on_insufficient_cash,
                run_type=RUN_TYPE.BACKTEST,
            )
        ),
        add_frontend_validator=lambda _validator: None,
    )


def make_mod_config(validate_cash):
    return SimpleNamespace(
        validate_price=False,
        validate_is_trading=False,
        validate_cash=validate_cash,
        validate_self_trade=False,
    )


def test_warns_when_partial_fill_is_enabled_without_cash_validation(monkeypatch):
    warnings = []
    monkeypatch.setattr(
        risk_mod,
        "user_system_log",
        SimpleNamespace(warning=warnings.append),
    )

    RiskManagerMod().start_up(
        make_env(partial_fill_on_insufficient_cash=True),
        make_mod_config(validate_cash=False),
    )

    assert warnings == [
        "partial_fill_on_insufficient_cash is enabled, while validate_cash has been explicitly "
        "disabled. Please confirm that this configuration is intended."
    ]


@pytest.mark.parametrize(
    "partial_fill_on_insufficient_cash, validate_cash",
    [(False, False), (True, True)],
)
def test_does_not_warn_for_other_cash_validation_configurations(
    monkeypatch,
    partial_fill_on_insufficient_cash,
    validate_cash,
):
    warnings = []
    monkeypatch.setattr(
        risk_mod,
        "user_system_log",
        SimpleNamespace(warning=warnings.append),
    )

    RiskManagerMod().start_up(
        make_env(partial_fill_on_insufficient_cash),
        make_mod_config(validate_cash),
    )

    assert warnings == []
