import logging

import pandas as pd
import pytest
from langgraph.prebuilt.tool_node import ToolInvocationError
from pydantic import BaseModel, Field, ValidationError

from app.errors import InvalidInputError, handle_tool_errors
from app.tools.customer import find_customer_by_cpf

GENERIC_SYSTEM_ERROR_MESSAGE = (
    "[ERRO DE SISTEMA] Uma ferramenta interna falhou. Explique ao cliente, sem detalhes técnicos, "
    "que há uma instabilidade nesta funcionalidade e peça desculpas."
)


class _Args(BaseModel):
    cpf: str = Field(pattern=r"^\d{11}$")


def _make_tool_invocation_error(tool_name: str, kwargs: dict) -> ToolInvocationError:
    try:
        _Args(**kwargs)
    except ValidationError as source:
        return ToolInvocationError(tool_name, source=source, tool_kwargs=kwargs)
    raise AssertionError("expected validation to fail")


def test_invalid_input_error_returns_prefixed_message_and_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = handle_tool_errors(InvalidInputError("CPF deve ter 11 dígitos."))

    assert result == "[ENTRADA INVÁLIDA] CPF deve ter 11 dígitos."
    assert any(r.levelname == "WARNING" for r in caplog.records)


def test_tool_invocation_error_returns_field_message_and_logs_warning(caplog):
    error = _make_tool_invocation_error("validate_customer", {"cpf": "123"})

    with caplog.at_level(logging.WARNING):
        result = handle_tool_errors(error)

    assert result == f"[ENTRADA INVÁLIDA] {error.message}"
    assert any(r.levelname == "WARNING" for r in caplog.records)


def test_invalid_input_and_tool_invocation_errors_do_not_touch_error_csv(tmp_csvs, caplog):
    handle_tool_errors(InvalidInputError("CPF inválido"))
    handle_tool_errors(_make_tool_invocation_error("validate_customer", {"cpf": "123"}))

    df = pd.read_csv(tmp_csvs["erros_sistema"])
    assert df.empty


def test_generic_exception_returns_fixed_message_without_leaking_details(tmp_csvs, monkeypatch, caplog):
    import app.tools.customer as customer_mod

    monkeypatch.setattr(customer_mod, "CLIENTES_CSV", tmp_csvs["clientes"].parent / "does_not_exist.csv")

    with pytest.raises(FileNotFoundError) as exc_info:
        find_customer_by_cpf("11111111111")

    with caplog.at_level(logging.ERROR):
        result = handle_tool_errors(exc_info.value)

    assert result == GENERIC_SYSTEM_ERROR_MESSAGE
    assert "does_not_exist" not in result
    assert "FileNotFoundError" not in result
    assert any(r.levelname == "ERROR" for r in caplog.records)


def test_generic_exception_records_tool_name_and_details_in_error_csv(tmp_csvs, monkeypatch):
    import app.tools.customer as customer_mod

    monkeypatch.setattr(customer_mod, "CLIENTES_CSV", tmp_csvs["clientes"].parent / "does_not_exist.csv")

    with pytest.raises(FileNotFoundError) as exc_info:
        find_customer_by_cpf("11111111111")

    handle_tool_errors(exc_info.value)

    df = pd.read_csv(tmp_csvs["erros_sistema"])
    assert len(df) == 1
    row = df.iloc[0]
    assert row["tool"] == "find_customer_by_cpf"
    assert row["exception_type"] == "FileNotFoundError"
    assert "does_not_exist" in row["message"]
