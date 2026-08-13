from langchain_core.messages import AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent

from app.agents.score_interview.prompt import build_score_interview_prompt
from app.errors import handle_tool_errors
from app.agents.llm import llm
from app.agents.message_history import trim_history
from app.schemas.state import GraphState
from app.tools.score import calculate_credit_score
from app.tools.system import end_conversation


def _score_interview_prompt(state: GraphState) -> list:
    print(f"[DEBUG _score_interview_prompt] credit_score_hops={state.get('credit_score_hops', 0)!r}")
    system = build_score_interview_prompt(customer=state["customer"])
    return [SystemMessage(content=system), *trim_history(state["messages"])]


def _post_model_hook(state: GraphState) -> dict:
    last = state["messages"][-1]
    print(
        f"[DEBUG score_interview post_model_hook] type={type(last).__name__} "
        f"content={getattr(last, 'content', None)!r} "
        f"tool_calls={getattr(last, 'tool_calls', None)!r} "
        f"usage_metadata={getattr(last, 'usage_metadata', None)!r}"
    )
    is_final_text_reply = isinstance(last, AIMessage) and not last.tool_calls
    if is_final_text_reply and state.get("score_recalculated", False):
        return {"current_agent": "credit"}
    return {}


score_interview_agent = create_react_agent(
    model=llm,
    tools=ToolNode(
        [
            calculate_credit_score,
            end_conversation,
        ],
        handle_tool_errors=handle_tool_errors,
    ),
    prompt=_score_interview_prompt,
    state_schema=GraphState,
    post_model_hook=_post_model_hook,
)
