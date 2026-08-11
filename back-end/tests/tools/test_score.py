import pytest

from app.schemas.tables import Customer
from app.tools.score import calculate_credit_score

_CUSTOMER = Customer(
    cpf="11111111111", nome="Ana Silva", data_nascimento="1990-05-12", score=750, limite_credito=5000.0
)


def test_calculate_credit_score_returns_incomplete_message_when_missing_data(tmp_csvs):
    state = {
        "messages": [],
        "customer": _CUSTOMER,
        "pending_income": 3000.0,
        "pending_employment_type": None,
        "pending_expenses": 1000.0,
        "pending_dependents": 1,
        "pending_has_debt": False,
    }

    command = calculate_credit_score(state=state, tool_call_id="test")

    assert command.update["messages"][0].content == "Dados da entrevista incompletos."


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
    state = {
        "messages": [],
        "customer": _CUSTOMER,
        "pending_income": income,
        "pending_employment_type": employment_type,
        "pending_expenses": expenses,
        "pending_dependents": dependents,
        "pending_has_debt": has_debt,
    }

    command = calculate_credit_score(state=state, tool_call_id="test")

    assert command.update["customer"].score == expected_score
    assert str(expected_score) in command.update["messages"][0].content
