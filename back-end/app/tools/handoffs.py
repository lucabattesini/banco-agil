from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.errors import InvalidInputError
from app.schemas.state import GraphState

_NOT_AUTHENTICATED_YET = (
    "O cliente ainda não terminou de ser autenticado nesta rodada — espere o resultado de "
    "`validate_customer` antes de redirecionar."
)

_MAX_CREDIT_SCORE_HOPS = 2
_CREDIT_SCORE_LOOP_BLOCKED = (
    "[REDIRECIONAMENTO BLOQUEADO] Crédito e Entrevista de Score já se alternaram demais nesta "
    "rodada e não chegaram a uma conclusão. Não tente redirecionar de novo — explique ao cliente, "
    "com clareza e educadamente, que não foi possível concluir automaticamente agora, e pergunte "
    "se há algo mais em que você pode ajudar."
)


def route_to_credit(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Route to the credit agent: limit checks/increases only. Not for score (route_to_score_interview)
    or exchange rate (route_to_exchange) questions. Call only after validate_customer succeeds — never
    in the same tool-call batch."""
    if state.get("customer") is None:
        raise InvalidInputError(_NOT_AUTHENTICATED_YET)

    hops = state.get("credit_score_hops", 0)
    if hops >= _MAX_CREDIT_SCORE_HOPS:
        raise InvalidInputError(_CREDIT_SCORE_LOOP_BLOCKED)

    return Command(
        goto="credit",
        update={
            "current_agent": "credit",
            "customer": state.get("customer"),
            "credit_score_hops": hops + 1,
            "score_reassessed": state.get("score_reassessed", False),
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )


def route_to_score_interview(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Route to the score interview agent: updating/improving credit score only. Not for credit limit
    (route_to_credit) or exchange rate (route_to_exchange) questions. Call only after validate_customer
    succeeds — never in the same tool-call batch."""
    if state.get("customer") is None:
        raise InvalidInputError(_NOT_AUTHENTICATED_YET)

    hops = state.get("credit_score_hops", 0)
    if hops >= _MAX_CREDIT_SCORE_HOPS:
        raise InvalidInputError(_CREDIT_SCORE_LOOP_BLOCKED)

    return Command(
        goto="score_interview",
        update={
            "current_agent": "score_interview",
            "customer": state.get("customer"),
            "credit_score_hops": hops + 1,
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )


def route_to_exchange(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Route to the exchange agent: currency exchange rate questions only. Not for credit limit
    (route_to_credit) or score (route_to_score_interview) questions. Call only after validate_customer
    succeeds — never in the same tool-call batch."""
    if state.get("customer") is None:
        raise InvalidInputError(_NOT_AUTHENTICATED_YET)

    return Command(
        goto="exchange",
        update={
            "current_agent": "exchange",
            "customer": state.get("customer"),
            "messages": [ToolMessage(content="", tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )


def return_to_triage(
    state: Annotated[GraphState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Return the conversation to the triage agent because the customer's request is outside your scope.

    Not currently offered to any agent — every message is routed through triage on every turn instead
    (see app/graph/builder.py), which is slower per turn but structurally immune to redirect loops. This
    tool is kept implemented and tested as a future optimization: a specialist could redirect directly
    without waiting for triage to re-process the next message, saving a model call and some latency, once
    the conditions for doing so safely (without reintroducing loops) are worked out.
    """
    bouncing_agent = state.get("current_agent")
    already_bounced = bouncing_agent is not None and bouncing_agent == state.get("last_bounced_agent")

    if already_bounced:
        content = (
            f"[REDIRECIONAMENTO BLOQUEADO] Você já tentou redirecionar o cliente para {bouncing_agent} "
            "nesta interação e não deu certo. Não tente de novo — explique ao cliente, com clareza e "
            "educadamente, que não é possível ajudá-lo com essa solicitação específica agora, e "
            "pergunte se há algo mais em que você pode ajudar."
        )
    else:
        content = ""

    return Command(
        goto="triage",
        update={
            "current_agent": "triage",
            "customer": state.get("customer"),
            "last_bounced_agent": bouncing_agent,
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        },
        graph=Command.PARENT,
    )
