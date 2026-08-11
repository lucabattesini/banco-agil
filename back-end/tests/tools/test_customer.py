import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.tools.customer import validate_customer

_VALIDATE_CUSTOMER_SCHEMA = StructuredTool.from_function(func=validate_customer).args_schema


@pytest.mark.parametrize("bad_cpf", ["123", "abc12345678", "123.456.789-00", "1234567890123"])
def test_validate_customer_rejects_malformed_cpf(bad_cpf):
    with pytest.raises(ValidationError):
        _VALIDATE_CUSTOMER_SCHEMA(cpf=bad_cpf, birth_date="2000-01-01", state={"messages": []}, tool_call_id="test")


@pytest.mark.parametrize("bad_date", ["12-01-2000", "2000/01/12", "2000-1-1", "not-a-date"])
def test_validate_customer_rejects_malformed_birth_date(bad_date):
    with pytest.raises(ValidationError):
        _VALIDATE_CUSTOMER_SCHEMA(cpf="11111111111", birth_date=bad_date, state={"messages": []}, tool_call_id="test")


def test_validate_customer_accepts_well_formed_input():
    _VALIDATE_CUSTOMER_SCHEMA(cpf="11111111111", birth_date="2000-01-01", state={"messages": []}, tool_call_id="test")
