from datetime import datetime, timezone
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.repositories import clientes_repository, score_limite_repository, solicitacoes_repository
from app.schemas.state import GraphState
from app.schemas.tables import LimitIncreaseRequest
from app.validators import CpfField, PositiveAmountField


def get_credit_limit(
    cpf: CpfField,
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Look up the customer's current available credit limit.

    Only call for an already authenticated customer.
    """
    customer = clientes_repository.find_by_cpf(cpf)

    if customer is None:
        return Command(
            update={"messages": [ToolMessage(content="Cliente não encontrado.", tool_call_id=tool_call_id)]}
        )

    updated_customer = state["customer"].model_copy(update={"limite_credito": customer.limite_credito})

    return Command(
        update={
            "customer": updated_customer,
            "messages": [
                ToolMessage(
                    content=f"Limite de crédito atual: {customer.limite_credito}", tool_call_id=tool_call_id
                )
            ],
        }
    )


def check_score_eligibility(score: int, requested_limit: float) -> dict:
    score_range = score_limite_repository.find_range_for_score(score)

    if score_range is None:
        return {"eligible": False, "limite_maximo": 0.0}

    return {"eligible": requested_limit <= score_range.limite_maximo, "limite_maximo": score_range.limite_maximo}


def register_limit_increase_request(
    cpf: CpfField,
    requested_limit: PositiveAmountField,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Register a credit limit increase request and resolve it as approved or rejected based on the customer's score.

    This creates a permanent record — only call once, after the customer has clearly stated the desired new limit.
    """
    customer = clientes_repository.find_by_cpf(cpf)
    if customer is None:
        return Command(
            update={"messages": [ToolMessage(content="Cliente não encontrado.", tool_call_id=tool_call_id)]}
        )

    eligibility = check_score_eligibility(customer.score, requested_limit)
    status = "aprovado" if eligibility["eligible"] else "rejeitado"

    solicitacoes_repository.create(
        LimitIncreaseRequest(
            cpf_cliente=cpf,
            data_hora_solicitacao=datetime.now(timezone.utc).isoformat(),
            limite_atual=customer.limite_credito,
            novo_limite_solicitado=requested_limit,
            status_pedido=status,
        )
    )

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Solicitação de aumento de limite para {requested_limit} registrada: {status}.",
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )
