from typing import Annotated, NotRequired, Optional, TypedDict

from langgraph.graph.message import add_messages
from langgraph.managed.is_last_step import RemainingSteps

from app.schemas.tables import Customer


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    customer: NotRequired[Optional[Customer]]
    auth_attempts: NotRequired[int]
    current_agent: NotRequired[str]
    pending_cpf: NotRequired[Optional[str]]
    pending_birth_date: NotRequired[Optional[str]]
    pending_requested_limit: NotRequired[Optional[float]]
    pending_income: NotRequired[Optional[float]]
    pending_employment_type: NotRequired[Optional[str]]
    pending_expenses: NotRequired[Optional[float]]
    pending_dependents: NotRequired[Optional[int]]
    pending_has_debt: NotRequired[Optional[bool]]
    conversation_ended: NotRequired[bool]
    remaining_steps: NotRequired[RemainingSteps]
