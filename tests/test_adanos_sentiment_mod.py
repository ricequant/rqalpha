# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from rqalpha.const import EXECUTION_PHASE
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.mod.rqalpha_mod_adanos_sentiment import load_mod


def _mod_config(**kwargs):
    config = {
        "api_key": "test-key",
        "base_url": "https://api.adanos.org",
        "source": "reddit",
        "timeout": 10,
    }
    config.update(kwargs)
    return SimpleNamespace(**config)


def _mock_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_adanos_sentiment_requests_single_stock():
    mod = load_mod()
    mod.start_up(None, _mod_config(source=" Reddit ", base_url="https://api.adanos.org/"))

    with patch(
        "rqalpha.mod.rqalpha_mod_adanos_sentiment.mod.requests.get",
        return_value=_mock_response({"ticker": "TSLA", "sentiment_score": 0.25}),
    ) as mock_get:
        result = mod.get_sentiment(" tsla.us ", days=3)

    assert result["ticker"] == "TSLA"
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.adanos.org/reddit/stocks/v1/stock/TSLA"
    assert kwargs["params"] == {"days": 3}
    assert kwargs["headers"]["X-API-Key"] == "test-key"
    assert kwargs["headers"]["Accept"] == "application/json"
    assert kwargs["timeout"] == 10


def test_adanos_sentiment_compare_accepts_iterables():
    mod = load_mod()
    mod.start_up(None, _mod_config(source="news"))

    with patch(
        "rqalpha.mod.rqalpha_mod_adanos_sentiment.mod.requests.get",
        return_value=_mock_response({"stocks": [{"ticker": "TSLA"}, {"ticker": "NVDA"}]}),
    ) as mock_get:
        result = mod.compare_sentiment(["TSLA.US", " nvda "], days=5)

    assert [item["ticker"] for item in result["stocks"]] == ["TSLA", "NVDA"]
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.adanos.org/news/stocks/v1/compare"
    assert kwargs["params"] == {"tickers": "TSLA,NVDA", "days": 5}


def test_adanos_sentiment_compare_accepts_comma_separated_string():
    mod = load_mod()
    mod.start_up(None, _mod_config(source="polymarket"))

    with patch(
        "rqalpha.mod.rqalpha_mod_adanos_sentiment.mod.requests.get",
        return_value=_mock_response({"stocks": []}),
    ) as mock_get:
        mod.compare_sentiment("tsla.us, nvda", days=7)

    _, kwargs = mock_get.call_args
    assert kwargs["params"] == {"tickers": "TSLA,NVDA", "days": 7}


def test_adanos_sentiment_uses_environment_api_key(monkeypatch):
    monkeypatch.setenv("ADANOS_API_KEY", "env-key")
    mod = load_mod()
    mod.start_up(None, _mod_config(api_key=""))

    with patch(
        "rqalpha.mod.rqalpha_mod_adanos_sentiment.mod.requests.get",
        return_value=_mock_response({"ticker": "AAPL"}),
    ) as mock_get:
        mod.get_sentiment("AAPL")

    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["X-API-Key"] == "env-key"


def test_adanos_sentiment_requires_api_key(monkeypatch):
    monkeypatch.delenv("ADANOS_API_KEY", raising=False)
    mod = load_mod()
    mod.start_up(None, _mod_config(api_key=""))

    with pytest.raises(ValueError, match="Please set mod.api_key"):
        mod.get_sentiment("AAPL")


def test_adanos_sentiment_validates_source_and_symbol():
    mod = load_mod()

    with pytest.raises(ValueError, match="source must be one of"):
        mod.start_up(None, _mod_config(source="invalid"))

    mod.start_up(None, _mod_config())
    with pytest.raises(ValueError, match="order_book_id must not be empty"):
        mod.get_sentiment(" ")


def test_adanos_sentiment_exports_strategy_api():
    mod = load_mod()
    mod.start_up(None, _mod_config())

    from rqalpha.api import adanos_sentiment

    with patch.object(
        mod,
        "get_sentiment",
        return_value={"ticker": "TSLA"},
    ) as mock_get_sentiment:
        with ExecutionContext(EXECUTION_PHASE.ON_BAR):
            result = adanos_sentiment("TSLA.US", source="x", days=2)

    assert result == {"ticker": "TSLA"}
    mock_get_sentiment.assert_called_once_with("TSLA.US", source="x", days=2)


def test_adanos_sentiment_compare_exports_strategy_api():
    mod = load_mod()
    mod.start_up(None, _mod_config())

    from rqalpha.api import adanos_sentiment_compare

    with patch.object(
        mod,
        "compare_sentiment",
        return_value={"stocks": [{"ticker": "TSLA"}]},
    ) as mock_compare_sentiment:
        with ExecutionContext(EXECUTION_PHASE.ON_BAR):
            result = adanos_sentiment_compare(["TSLA.US"], source="news", days=4)

    assert result == {"stocks": [{"ticker": "TSLA"}]}
    mock_compare_sentiment.assert_called_once_with(["TSLA.US"], source="news", days=4)
