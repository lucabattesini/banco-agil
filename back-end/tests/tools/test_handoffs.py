import pytest

from app.errors import InvalidInputError
from app.schemas.tables import Customer
from app.tools.handoffs import return_to_triage, route_to_credit, route_to_exchange, route_to_score_interview

_CUSTOMER = Customer(
    cpf="11111111111", nome="Ana Silva", data_nascimento="1990-05-12", score=750, limite_credito=5000.0
)


def test_route_to_credit_carries_customer_across_the_handoff():
    command = route_to_credit(state={"customer": _CUSTOMER}, tool_call_id="test")

    assert command.goto == "credit"
    assert command.update["current_agent"] == "credit"
    assert command.update["customer"] == _CUSTOMER


def test_route_to_score_interview_carries_customer_across_the_handoff():
    command = route_to_score_interview(state={"customer": _CUSTOMER}, tool_call_id="test")

    assert command.goto == "score_interview"
    assert command.update["current_agent"] == "score_interview"
    assert command.update["customer"] == _CUSTOMER


def test_route_to_exchange_carries_customer_across_the_handoff():
    command = route_to_exchange(state={"customer": _CUSTOMER}, tool_call_id="test")

    assert command.goto == "exchange"
    assert command.update["current_agent"] == "exchange"
    assert command.update["customer"] == _CUSTOMER


def test_return_to_triage_carries_customer_across_the_handoff():
    command = return_to_triage(state={"customer": _CUSTOMER, "current_agent": "credit"}, tool_call_id="test")

    assert command.goto == "triage"
    assert command.update["current_agent"] == "triage"
    assert command.update["customer"] == _CUSTOMER


def test_return_to_triage_first_bounce_is_neutral_and_records_the_agent():
    command = return_to_triage(
        state={"customer": _CUSTOMER, "current_agent": "credit", "last_bounced_agent": None},
        tool_call_id="test",
    )

    assert command.update["last_bounced_agent"] == "credit"
    assert command.update["messages"][0].content == ""


def test_return_to_triage_repeated_bounce_from_the_same_agent_is_blocked():
    command = return_to_triage(
        state={"customer": _CUSTOMER, "current_agent": "credit", "last_bounced_agent": "credit"},
        tool_call_id="test",
    )

    assert "REDIRECIONAMENTO BLOQUEADO" in command.update["messages"][0].content
    assert command.update["last_bounced_agent"] == "credit"


def test_return_to_triage_bounce_from_a_different_agent_is_not_blocked():
    command = return_to_triage(
        state={"customer": _CUSTOMER, "current_agent": "exchange", "last_bounced_agent": "credit"},
        tool_call_id="test",
    )

    assert command.update["messages"][0].content == ""
    assert command.update["last_bounced_agent"] == "exchange"


@pytest.mark.parametrize("route", [route_to_credit, route_to_score_interview, route_to_exchange])
def test_route_rejects_handoff_before_customer_is_authenticated(route):
    """Guards against a model calling validate_customer and a route_to_* tool in the same
    parallel batch — InjectedState for route_to_* still reflects the pre-batch snapshot in that
    case, so customer would otherwise be silently forwarded as None."""
    with pytest.raises(InvalidInputError):
        route(state={"customer": None}, tool_call_id="test")
