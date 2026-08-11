from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.repositories import clientes_repository
from app.schemas.state import GraphState

PESO_RENDA = 30
PESO_EMPREGO = {"formal": 300, "autônomo": 200, "desempregado": 0}
PESO_DEPENDENTES = {0: 100, 1: 80, 2: 60}
PESO_DEPENDENTES_3_PLUS = 30
PESO_DIVIDA_SIM = -100
PESO_DIVIDA_NAO = 100


def calculate_credit_score(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Calculate the customer's new credit score from the interview answers and persist it.

    Only call once all five interview answers (income, employment type, expenses, dependents, debt) are known.
    """
    required = [
        state.get("pending_income"),
        state.get("pending_employment_type"),
        state.get("pending_expenses"),
        state.get("pending_dependents"),
        state.get("pending_has_debt"),
    ]
    if any(value is None for value in required):
        return Command(
            update={"messages": [ToolMessage(content="Dados da entrevista incompletos.", tool_call_id=tool_call_id)]}
        )

    peso_dependentes = PESO_DEPENDENTES.get(state["pending_dependents"], PESO_DEPENDENTES_3_PLUS)
    peso_divida = PESO_DIVIDA_SIM if state["pending_has_debt"] else PESO_DIVIDA_NAO

    score = (
        (state["pending_income"] / (state["pending_expenses"] + 1)) * PESO_RENDA
        + PESO_EMPREGO[state["pending_employment_type"]]
        + peso_dependentes
        + peso_divida
    )
    new_score = int(max(0, min(1000, score)))

    success = clientes_repository.update_score(state["customer"].cpf, new_score)
    if not success:
        return Command(
            update={"messages": [ToolMessage(content="Não foi possível salvar o novo score.", tool_call_id=tool_call_id)]}
        )

    updated_customer = state["customer"].model_copy(update={"score": new_score})
    return Command(
        update={
            "customer": updated_customer,
            "messages": [ToolMessage(content=f"Novo score calculado e salvo: {new_score}", tool_call_id=tool_call_id)],
        }
    )
