from app.schemas.tables import Customer
from app.tools.handoffs import route_to_credit, route_to_exchange, route_to_score_interview

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
