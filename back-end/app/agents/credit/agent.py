from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.credit.prompt import build_credit_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.credit import get_credit_limit, register_limit_increase_request
from app.tools.handoffs import route_to_score_interview
from app.tools.system import end_conversation


def _credit_prompt(state: GraphState) -> list:
    print(f"[DEBUG _credit_prompt] credit_score_hops={state.get('credit_score_hops', 0)!r}")
    system = build_credit_prompt(
        customer=state["customer"],
        score_recalculated=state.get("score_recalculated", False),
        pending_limit_retry=state.get("pending_limit_retry"),
    )
    return [SystemMessage(content=system), *trim_history(state["messages"])]


def _debug_post_model_hook(state: GraphState) -> dict:
    last = state["messages"][-1]
    print(
        f"[DEBUG credit post_model_hook] type={type(last).__name__} "
        f"content={getattr(last, 'content', None)!r} "
        f"tool_calls={getattr(last, 'tool_calls', None)!r} "
        f"usage_metadata={getattr(last, 'usage_metadata', None)!r}"
    )
    is_final_text_reply = isinstance(last, AIMessage) and not last.tool_calls
    if is_final_text_reply and state.get("score_recalculated", False):
        return {"score_recalculated": False}
    return {}


credit_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            get_credit_limit,
            register_limit_increase_request,
            route_to_score_interview,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_credit_prompt,
    state_schema=GraphState,
    post_model_hook=_debug_post_model_hook,
)
