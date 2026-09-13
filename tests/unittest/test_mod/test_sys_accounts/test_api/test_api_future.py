from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from rqalpha.const import POSITION_DIRECTION, POSITION_EFFECT, SIDE
from rqalpha.environment import Environment
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_future import _order, _submit_order


def _environment_with_positions(long_position, short_position):
    positions = {
        POSITION_DIRECTION.LONG: long_position,
        POSITION_DIRECTION.SHORT: short_position,
    }
    portfolio = SimpleNamespace(
        get_position=lambda _id, direction: positions[direction]
    )
    return SimpleNamespace(portfolio=portfolio, order_creation_failed=Mock())


def test_submit_order_zero_quantity_returns_none():
    env = SimpleNamespace(order_creation_failed=Mock())

    with patch.object(Environment, "get_instance", return_value=env):
        result = _submit_order("IF88", 0, SIDE.BUY, POSITION_EFFECT.OPEN, None)

    assert result is None
    env.order_creation_failed.assert_called_once()


def test_order_to_same_target_returns_empty_without_order():
    env = _environment_with_positions(
        SimpleNamespace(quantity=1, old_quantity=1, today_quantity=0),
        SimpleNamespace(quantity=0, old_quantity=0, today_quantity=0),
    )

    with patch.object(Environment, "get_instance", return_value=env):
        result = _order("IF88", 1, None, target=True)

    assert result == []
    env.order_creation_failed.assert_not_called()


@pytest.mark.parametrize("submission_result", [None, []])
def test_order_drops_empty_submission_result(submission_result):
    env = _environment_with_positions(
        SimpleNamespace(quantity=0, old_quantity=0, today_quantity=0),
        SimpleNamespace(quantity=0, old_quantity=0, today_quantity=0),
    )

    with patch.object(Environment, "get_instance", return_value=env), patch(
        "rqalpha.mod.rqalpha_mod_sys_accounts.api.api_future._submit_order",
        return_value=submission_result,
    ):
        result = _order("IF88", 1, None, target=False)

    assert result == []
