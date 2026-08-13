from typing import Annotated, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.repositories import clientes_repository
from app.schemas.state import GraphState
from app.schemas.validators import DependentsField, NonNegativeAmountField

PESO_RENDA = 30
PESO_EMPREGO = {"formal": 300, "autônomo": 200, "desempregado": 0}
PESO_DEPENDENTES = {0: 100, 1: 80, 2: 60}
PESO_DEPENDENTES_3_PLUS = 30
PESO_DIVIDA_SIM = -100
PESO_DIVIDA_NAO = 100


def calculate_credit_score(
    income: NonNegativeAmountField,
    employment_type: Literal["formal", "autônomo", "desempregado"],
    expenses: NonNegativeAmountField,
    dependents: DependentsField,
    has_debt: bool,
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Calculate the customer's new credit score from the interview answers and persist it.

    Call once all five interview answers are known: income, employment type, expenses, dependents, debt.
    """
    peso_dependentes = PESO_DEPENDENTES.get(dependents, PESO_DEPENDENTES_3_PLUS)
    peso_divida = PESO_DIVIDA_SIM if has_debt else PESO_DIVIDA_NAO

    score = (income / (expenses + 1)) * PESO_RENDA + PESO_EMPREGO[employment_type] + peso_dependentes + peso_divida
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
