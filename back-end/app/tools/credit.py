from datetime import datetime, timezone
from typing import Annotated

import pandas as pd
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.config import CLIENTES_CSV, SCORE_LIMITE_CSV, SOLICITACOES_CSV
from app.schemas.state import GraphState
from app.tools.customer import find_customer_by_cpf
from app.validators import CpfField, PositiveAmountField


def get_credit_limit(
    cpf: CpfField,
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Look up the customer's current available credit limit.

    Only call for an already authenticated customer.
    """
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})
    match = df[df["cpf"] == cpf]

    if match.empty:
        return Command(
            update={"messages": [ToolMessage(content="Cliente não encontrado.", tool_call_id=tool_call_id)]}
        )

    limite_credito = float(match.iloc[0]["limite_credito"])
    updated_customer = state["customer"].model_copy(update={"limite_credito": limite_credito})

    return Command(
        update={
            "customer": updated_customer,
            "messages": [
                ToolMessage(content=f"Limite de crédito atual: {limite_credito}", tool_call_id=tool_call_id)
            ],
        }
    )


def check_score_eligibility(score: int, requested_limit: float) -> dict:
    df = pd.read_csv(SCORE_LIMITE_CSV)
    match = df[(df["score_min"] <= score) & (score <= df["score_max"])]

    if match.empty:
        return {"eligible": False, "limite_maximo": 0.0}

    limite_maximo = float(match.iloc[0]["limite_maximo"])
    return {"eligible": requested_limit <= limite_maximo, "limite_maximo": limite_maximo}


def register_limit_increase_request(
    cpf: CpfField,
    requested_limit: PositiveAmountField,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Register a credit limit increase request and resolve it as approved or rejected based on the customer's score.

    This creates a permanent record — only call once, after the customer has clearly stated the desired new limit.
    """
    customer = find_customer_by_cpf(cpf)
    if customer is None:
        return Command(
            update={"messages": [ToolMessage(content="Cliente não encontrado.", tool_call_id=tool_call_id)]}
        )

    score = int(customer["score"])
    current_limit = float(customer["limite_credito"])

    eligibility = check_score_eligibility(score, requested_limit)
    status = "aprovado" if eligibility["eligible"] else "rejeitado"

    df = pd.read_csv(SOLICITACOES_CSV, dtype={"cpf_cliente": str})
    new_row = {
        "cpf_cliente": cpf,
        "data_hora_solicitacao": datetime.now(timezone.utc).isoformat(),
        "limite_atual": current_limit,
        "novo_limite_solicitado": requested_limit,
        "status_pedido": status,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(SOLICITACOES_CSV, index=False)

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
