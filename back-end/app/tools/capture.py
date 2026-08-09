from typing import Annotated, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command


def capture_auth_data(
    cpf: Optional[str] = None,
    birth_date: Optional[str] = None,
    *,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Store the CPF and/or birth date as they are provided by the customer, even if only one is known so far.

    cpf must be digits only (no dots or dashes); birth_date must be in YYYY-MM-DD format.
    Call this as soon as either value is identified — do not wait until both are known.
    """
    update = {"messages": [ToolMessage(content="Dado(s) registrado(s).", tool_call_id=tool_call_id)]}
    if cpf is not None:
        update["pending_cpf"] = cpf
    if birth_date is not None:
        update["pending_birth_date"] = birth_date

    return Command(update=update)


def capture_requested_limit(
    requested_limit: float,
    *,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Store the new credit limit amount requested by the customer.

    Call as soon as the customer states a clear number, before calling register_limit_increase_request.
    """
    return Command(
        update={
            "pending_requested_limit": requested_limit,
            "messages": [ToolMessage(content="Valor solicitado registrado.", tool_call_id=tool_call_id)],
        }
    )


def capture_interview_data(
    income: Optional[float] = None,
    employment_type: Optional[str] = None,
    expenses: Optional[float] = None,
    dependents: Optional[int] = None,
    has_debt: Optional[bool] = None,
    *,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Store the customer's financial interview answers as they are provided, even if only some are known so far.

    employment_type must be one of: "formal", "autônomo", "desempregado".
    Call this as soon as any value is identified — do not wait until all five are known.
    """
    update = {"messages": [ToolMessage(content="Dado(s) da entrevista registrado(s).", tool_call_id=tool_call_id)]}
    if income is not None:
        update["pending_income"] = income
    if employment_type is not None:
        update["pending_employment_type"] = employment_type
    if expenses is not None:
        update["pending_expenses"] = expenses
    if dependents is not None:
        update["pending_dependents"] = dependents
    if has_debt is not None:
        update["pending_has_debt"] = has_debt

    return Command(update=update)
