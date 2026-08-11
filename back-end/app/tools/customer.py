from typing import Annotated, Optional

import pandas as pd
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.config import CLIENTES_CSV
from app.schemas.state import GraphState
from app.schemas.tables import Customer
from app.validators import BirthDateField, CpfField


def find_customer_by_cpf(cpf: str) -> Optional[dict]:
    df = pd.read_csv(CLIENTES_CSV, dtype={"cpf": str})
    match = df[df["cpf"] == cpf]
    return match.iloc[0].to_dict() if not match.empty else None


def validate_customer(
    cpf: CpfField,
    birth_date: BirthDateField,
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Authenticate the customer by checking their CPF and birth date against the customer database.

    Only call once both values are known. Each failed attempt is counted automatically.
    """
    customer = find_customer_by_cpf(cpf)

    if customer is None or str(customer["data_nascimento"]) != birth_date:
        return Command(
            update={
                "auth_attempts": state.get("auth_attempts", 0) + 1,
                "pending_cpf": None,
                "pending_birth_date": None,
                "messages": [ToolMessage(content="Autenticação falhou.", tool_call_id=tool_call_id)],
            }
        )

    return Command(
        update={
            "customer": Customer(**customer),
            "messages": [ToolMessage(content="Cliente autenticado com sucesso.", tool_call_id=tool_call_id)],
        }
    )
