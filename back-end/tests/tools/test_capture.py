import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.tools.capture import capture_auth_data, capture_interview_data, capture_requested_limit

_CAPTURE_AUTH_DATA_SCHEMA = StructuredTool.from_function(func=capture_auth_data).args_schema
_CAPTURE_INTERVIEW_DATA_SCHEMA = StructuredTool.from_function(func=capture_interview_data).args_schema
_CAPTURE_REQUESTED_LIMIT_SCHEMA = StructuredTool.from_function(func=capture_requested_limit).args_schema


def test_capture_auth_data_stores_only_provided_fields():
    command = capture_auth_data(cpf="11111111111", tool_call_id="test")

    assert command.update["pending_cpf"] == "11111111111"
    assert "pending_birth_date" not in command.update


def test_capture_auth_data_stores_both_fields_when_both_provided():
    command = capture_auth_data(cpf="11111111111", birth_date="2000-01-01", tool_call_id="test")

    assert command.update["pending_cpf"] == "11111111111"
    assert command.update["pending_birth_date"] == "2000-01-01"


@pytest.mark.parametrize("bad_cpf", ["123", "abc12345678"])
def test_capture_auth_data_rejects_malformed_cpf(bad_cpf):
    with pytest.raises(ValidationError):
        _CAPTURE_AUTH_DATA_SCHEMA(cpf=bad_cpf, tool_call_id="test")


@pytest.mark.parametrize("bad_date", ["12-01-2000", "not-a-date"])
def test_capture_auth_data_rejects_malformed_birth_date(bad_date):
    with pytest.raises(ValidationError):
        _CAPTURE_AUTH_DATA_SCHEMA(birth_date=bad_date, tool_call_id="test")


def test_capture_auth_data_accepts_no_fields_provided():
    _CAPTURE_AUTH_DATA_SCHEMA(tool_call_id="test")


def test_capture_interview_data_stores_only_provided_fields():
    command = capture_interview_data(income=5000.0, tool_call_id="test")

    assert command.update["pending_income"] == 5000.0
    assert "pending_employment_type" not in command.update


def test_capture_interview_data_rejects_invalid_employment_type():
    with pytest.raises(ValidationError):
        _CAPTURE_INTERVIEW_DATA_SCHEMA(employment_type="estagiario", tool_call_id="test")


@pytest.mark.parametrize("employment_type", ["formal", "autônomo", "desempregado"])
def test_capture_interview_data_accepts_valid_employment_types(employment_type):
    _CAPTURE_INTERVIEW_DATA_SCHEMA(employment_type=employment_type, tool_call_id="test")


@pytest.mark.parametrize("field", ["income", "expenses", "dependents"])
def test_capture_interview_data_rejects_negative_values(field):
    with pytest.raises(ValidationError):
        _CAPTURE_INTERVIEW_DATA_SCHEMA(**{field: -1}, tool_call_id="test")


def test_capture_interview_data_accepts_zero_for_income_expenses_dependents():
    _CAPTURE_INTERVIEW_DATA_SCHEMA(income=0, expenses=0, dependents=0, tool_call_id="test")


@pytest.mark.parametrize("bad_value", [0, -1, -0.01])
def test_capture_requested_limit_rejects_non_positive_value(bad_value):
    with pytest.raises(ValidationError):
        _CAPTURE_REQUESTED_LIMIT_SCHEMA(requested_limit=bad_value, tool_call_id="test")


def test_capture_requested_limit_accepts_positive_value():
    _CAPTURE_REQUESTED_LIMIT_SCHEMA(requested_limit=500.0, tool_call_id="test")
