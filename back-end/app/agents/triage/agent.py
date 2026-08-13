from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.triage.prompt import build_triage_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.customer import validate_customer
from app.tools.handoffs import route_to_credit, route_to_exchange
from app.tools.system import end_conversation


def _triage_prompt(state: GraphState) -> list:
    print(
        f"[DEBUG _triage_prompt] auth_attempts={state.get('auth_attempts', 0)!r} "
        f"pending_cpf={state.get('pending_cpf')!r} pending_birth_date={state.get('pending_birth_date')!r}"
    )
    system = build_triage_prompt(
        auth_attempts=state.get("auth_attempts", 0),
        customer=state.get("customer"),
    )
    return [SystemMessage(content=system), *trim_history(state["messages"])]


def _debug_post_model_hook(state: GraphState) -> dict:
    last = state["messages"][-1]
    print(
        f"[DEBUG post_model_hook] type={type(last).__name__} "
        f"content={getattr(last, 'content', None)!r} "
        f"tool_calls={getattr(last, 'tool_calls', None)!r} "
        f"usage_metadata={getattr(last, 'usage_metadata', None)!r} "
        f"response_metadata={getattr(last, 'response_metadata', None)!r}"
    )
    return {}


triage_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            validate_customer,
            end_conversation,
            route_to_credit,
            route_to_exchange,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_triage_prompt,
    state_schema=GraphState,
    post_model_hook=_debug_post_model_hook,
)
