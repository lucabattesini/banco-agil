from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages

from app.schemas.tables import Customer


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    customer: Optional[Customer]
    auth_attempts: int
    current_agent: str
