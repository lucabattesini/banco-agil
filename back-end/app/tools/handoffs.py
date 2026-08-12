from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.schemas.state import GraphState


def route_to_credit(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Transfer the conversation to the credit agent.

    Use when the customer wants to check their available credit limit or request a limit increase.
    Do not use for credit score questions (use route_to_score_interview) or currency rates (use route_to_exchange).
    """
    return Command(
        goto="credit",
        update={
            "current_agent": "credit",
            "customer": state.get("customer"),
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )


def route_to_score_interview(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Transfer the conversation to the credit score interview agent.

    Use when the customer wants to update or improve their credit score.
    Do not use for credit limit questions (use route_to_credit) or currency rates (use route_to_exchange).
    """
    return Command(
        goto="score_interview",
        update={
            "current_agent": "score_interview",
            "customer": state.get("customer"),
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )


def route_to_exchange(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Transfer the conversation to the currency exchange agent.

    Use when the customer wants to check the exchange rate for a currency.
    Do not use for credit limit questions (use route_to_credit) or score questions (use route_to_score_interview).
    """
    return Command(
        goto="exchange",
        update={
            "current_agent": "exchange",
            "customer": state.get("customer"),
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )
