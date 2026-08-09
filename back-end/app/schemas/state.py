from typing import Annotated, NotRequired, Optional, TypedDict

from langgraph.graph.message import add_messages
from langgraph.managed.is_last_step import RemainingSteps

from app.schemas.tables import Customer


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    customer: Optional[Customer]
    auth_attempts: int
    current_agent: str
    pending_cpf: Optional[str]
    pending_birth_date: Optional[str]
    pending_requested_limit: Optional[float]
    pending_income: Optional[float]
    pending_employment_type: Optional[str]
    pending_expenses: Optional[float]
    pending_dependents: Optional[int]
    pending_has_debt: Optional[bool]
    conversation_ended: bool
    remaining_steps: NotRequired[RemainingSteps]
