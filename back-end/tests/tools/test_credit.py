import pandas as pd
import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.tools.credit import check_score_eligibility, get_credit_limit, register_limit_increase_request

_GET_CREDIT_LIMIT_SCHEMA = StructuredTool.from_function(func=get_credit_limit).args_schema
_REGISTER_LIMIT_INCREASE_SCHEMA = StructuredTool.from_function(func=register_limit_increase_request).args_schema


def test_check_score_eligibility_approves_within_limit(tmp_csvs):
    result = check_score_eligibility(score=750, requested_limit=5000.0)

    assert result == {"eligible": True, "limite_maximo": 6000.0}


def test_check_score_eligibility_rejects_above_limit(tmp_csvs):
    result = check_score_eligibility(score=750, requested_limit=7000.0)

    assert result == {"eligible": False, "limite_maximo": 6000.0}


def test_register_limit_increase_request_returns_not_found_message(tmp_csvs):
    command = register_limit_increase_request(
        cpf="99999999999", requested_limit=1000.0, state={"messages": []}, tool_call_id="test"
    )

    assert command.update["messages"][0].content == "Cliente não encontrado."


def test_register_limit_increase_request_approves_within_score_limit(tmp_csvs):
    command = register_limit_increase_request(
        cpf="11111111111", requested_limit=5000.0, state={"messages": []}, tool_call_id="test"
    )

    message = command.update["messages"][0].content
    assert "aprovado" in message
    assert message.startswith("Solicitação de aumento de limite")
    assert command.update["pending_limit_retry"] is None

    df = pd.read_csv(tmp_csvs["solicitacoes"])
    assert len(df) == 1
    assert df.iloc[0]["status_pedido"] == "aprovado"


def test_register_limit_increase_request_rejects_above_score_limit(tmp_csvs):
    command = register_limit_increase_request(
        cpf="11111111111", requested_limit=7000.0, state={"messages": []}, tool_call_id="test"
    )

    message = command.update["messages"][0].content
    assert "rejeitado" in message
    assert command.update["pending_limit_retry"] == 7000.0

    df = pd.read_csv(tmp_csvs["solicitacoes"])
    assert df.iloc[0]["status_pedido"] == "rejeitado"


@pytest.mark.parametrize("bad_cpf", ["123", "abc12345678"])
def test_get_credit_limit_rejects_malformed_cpf(bad_cpf):
    with pytest.raises(ValidationError):
        _GET_CREDIT_LIMIT_SCHEMA(cpf=bad_cpf, state={"messages": []}, tool_call_id="test")


@pytest.mark.parametrize("bad_cpf", ["123", "abc12345678"])
def test_register_limit_increase_request_rejects_malformed_cpf(bad_cpf):
    with pytest.raises(ValidationError):
        _REGISTER_LIMIT_INCREASE_SCHEMA(cpf=bad_cpf, requested_limit=1000.0, tool_call_id="test")


@pytest.mark.parametrize("bad_value", [0, -100])
def test_register_limit_increase_request_rejects_non_positive_limit(bad_value):
    with pytest.raises(ValidationError):
        _REGISTER_LIMIT_INCREASE_SCHEMA(cpf="11111111111", requested_limit=bad_value, tool_call_id="test")
