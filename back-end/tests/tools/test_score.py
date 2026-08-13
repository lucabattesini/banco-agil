import pytest
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.schemas.tables import Customer
from app.tools.score import calculate_credit_score

_CUSTOMER = Customer(
    cpf="11111111111", nome="Ana Silva", data_nascimento="1990-05-12", score=750, limite_credito=5000.0
)
_CALCULATE_CREDIT_SCORE_SCHEMA = StructuredTool.from_function(func=calculate_credit_score).args_schema
_VALID_KWARGS = {
    "income": 3000.0,
    "employment_type": "formal",
    "expenses": 1000.0,
    "dependents": 1,
    "has_debt": False,
    "state": {"messages": []},
    "tool_call_id": "test",
}


@pytest.mark.parametrize("missing_field", ["income", "employment_type", "expenses", "dependents", "has_debt"])
def test_calculate_credit_score_requires_all_five_interview_fields(missing_field):
    kwargs = {k: v for k, v in _VALID_KWARGS.items() if k != missing_field}

    with pytest.raises(ValidationError):
        _CALCULATE_CREDIT_SCORE_SCHEMA(**kwargs)


@pytest.mark.parametrize(
    "income,employment_type,expenses,dependents,has_debt,expected_score",
    [
        # (3000 / 1001) * 30 + 300 + 80 + 100 = 569.91... -> 569
        (3000.0, "formal", 1000.0, 1, False, 569),
        # (0 / 501) * 30 + 0 + 100 - 100 = 0
        (0.0, "desempregado", 500.0, 0, True, 0),
        # (10000 / 101) * 30 + 200 + 30 + 100 = 3300.29... -> clamped to 1000
        (10000.0, "autônomo", 100.0, 4, False, 1000),
    ],
)
def test_calculate_credit_score_formula(
    tmp_csvs, income, employment_type, expenses, dependents, has_debt, expected_score
):
    state = {"messages": [], "customer": _CUSTOMER}

    command = calculate_credit_score(
        income=income,
        employment_type=employment_type,
        expenses=expenses,
        dependents=dependents,
        has_debt=has_debt,
        state=state,
        tool_call_id="test",
    )

    assert command.update["customer"].score == expected_score
    assert command.update["score_recalculated"] is True
    assert str(expected_score) in command.update["messages"][0].content
