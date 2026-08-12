import httpx
import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.errors import InvalidInputError
from app.tools.exchange import get_exchange_rate

_GET_EXCHANGE_RATE_SCHEMA = StructuredTool.from_function(func=get_exchange_rate).args_schema


class _FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=httpx.Request("GET", "https://example.com"), response=self)

    def json(self):
        return self._json_data


@pytest.mark.parametrize("bad_currency", ["US", "usd", "USDD", "123"])
def test_get_exchange_rate_rejects_malformed_currency(bad_currency):
    with pytest.raises(ValidationError):
        _GET_EXCHANGE_RATE_SCHEMA(currency=bad_currency)


def test_get_exchange_rate_defaults_to_brl(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/USD-BRL")
        return _FakeResponse(200, {"USDBRL": {"bid": "5.30", "create_date": "2026-01-01 10:00:00"}})

    monkeypatch.setattr(httpx, "get", fake_get)

    result = get_exchange_rate(currency="USD")

    assert result == "1 USD = 5.30 BRL (atualizado em 2026-01-01 10:00:00)"


def test_get_exchange_rate_uses_explicit_compare_to(monkeypatch):
    def fake_get(url, timeout):
        assert url.endswith("/USD-EUR")
        return _FakeResponse(200, {"USDEUR": {"bid": "0.86", "create_date": "2026-01-01 10:00:00"}})

    monkeypatch.setattr(httpx, "get", fake_get)

    result = get_exchange_rate(currency="USD", compare_to="EUR")

    assert result == "1 USD = 0.86 EUR (atualizado em 2026-01-01 10:00:00)"


def test_get_exchange_rate_raises_invalid_input_for_unknown_pair(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda url, timeout: _FakeResponse(404, {"status": 404, "code": "CoinNotExists"}))

    with pytest.raises(InvalidInputError):
        get_exchange_rate(currency="XXX")


def test_get_exchange_rate_propagates_other_http_errors(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda url, timeout: _FakeResponse(500, {}))

    with pytest.raises(httpx.HTTPStatusError):
        get_exchange_rate(currency="USD")
